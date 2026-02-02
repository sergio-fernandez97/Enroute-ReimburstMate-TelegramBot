import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import psycopg
from psycopg import rows

from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState


class QueryStatus:
    """Query existing expense status from storage."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        load_dotenv()
        self._model = model
        self._prompt_text = self._load_prompt()
        self._chain = self._build_chain()

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.
            config: Node configuration.

        Returns:
            Updated workflow state.
        """
        logging.info("QueryStatus input state=%s", state)
        return self._query(state)

    def _query(self, state: WorkflowState) -> WorkflowState:
        """Query status data based on the user message."""
        response = self._invoke_llm(state.user_input or "")
        queries = response.queries
        if queries is None:
            return state

        status_rows = self._execute_queries(queries)
        return state.model_copy(update={"status_rows": status_rows})

    def _load_prompt(self) -> str:
        """Load the query status prompt text from disk."""
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "query_status.md"
        return prompt_path.read_text(encoding="utf-8").strip()

    def _build_chain(self):
        """Build the prompt -> LLM chain with structured output."""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._prompt_text),
                ("human", "User message:\n{user_message}"),
            ]
        )
        llm = ChatOpenAI(model=self._model)
        return prompt | llm.with_structured_output(QueryStatusResponse)

    def _invoke_llm(self, user_message: str) -> QueryStatusResponse:
        """Invoke the LLM chain and return the structured response."""
        return self._chain.invoke({"user_message": user_message})

    def _execute_queries(self, queries: list[str]) -> list[dict[str, Any]]:
        """Execute SQL queries and return collected rows."""
        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            logging.warning("QueryStatus skipped: DATABASE_URL not set.")
            return []

        results: list[dict[str, Any]] = []
        try:
            with psycopg.connect(database_url) as conn:
                with conn.cursor(row_factory=rows.dict_row) as cur:
                    for query in queries:
                        cleaned = (query or "").strip()
                        if not cleaned:
                            continue
                        if not cleaned.lower().startswith("select"):
                            logging.warning("QueryStatus skipped non-select query.")
                            continue
                        cur.execute(cleaned)
                        results.extend([dict(row) for row in cur.fetchall()])
        except Exception:
            logging.exception("QueryStatus failed to run queries.")
            return []

        return results
