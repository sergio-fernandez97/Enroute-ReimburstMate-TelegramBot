import logging
import os
from pathlib import Path
from typing import Any

import psycopg
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState


class QueryStatus:
    """Queries expense status information for the user."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        database_url: str | None = None,
        llm: ChatOpenAI | None = None,
    ) -> None:
        """Initialize the query status node.

        Args:
            model: OpenAI model name for query generation.
            database_url: Optional database URL override.
            llm: Optional LLM override for testing.
        """
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "query_status.md"
        self._prompt = prompt_path.read_text(encoding="utf-8").strip()
        self._llm = llm or ChatOpenAI(model=model, temperature=0)
        self._database_url = database_url or os.getenv("DATABASE_URL", "")

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("QueryStatus input state=%s", state)
        return self._query(state)

    def _query(self, state: WorkflowState) -> WorkflowState:
        """Generate SQL queries, execute them, and store results."""
        if not state.user_input:
            logging.info("QueryStatus skipped; user_input is missing")
            return state

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._prompt),
                ("human", "User message:\n{user_input}"),
            ]
        )
        chain = prompt | self._llm.with_structured_output(QueryStatusResponse)
        response = chain.invoke({"user_input": state.user_input})

        queries = response.queries
        if not queries:
            logging.info("QueryStatus returned no queries")
            return state

        status_rows = self._execute_queries(queries)
        return state.model_copy(update={"status_rows": status_rows})

    def _execute_queries(self, queries: list[str]) -> list[dict[str, Any]]:
        """Run SQL queries and return rows as dictionaries."""
        if not self._database_url:
            logging.warning("DATABASE_URL not set; skipping status query execution")
            return []

        results: list[dict[str, Any]] = []
        try:
            with psycopg.connect(self._database_url) as conn:
                with conn.cursor() as cur:
                    for query in queries:
                        cur.execute(query)
                        if not cur.description:
                            continue
                        columns = [column.name for column in cur.description]
                        for row in cur.fetchall():
                            results.append(dict(zip(columns, row)))
        except Exception:
            logging.exception("QueryStatus failed executing queries")
            return []

        return results
