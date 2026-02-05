import logging
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "query_status.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()
DEFAULT_MODEL = "gpt-4o-mini"


class QueryStatus:
    """Query expense status records for the requesting user."""

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
        """Retrieve status rows and update state."""
        chain = self._build_chain()
        user_message = state.user_input or ""
        response = self._invoke_llm(chain, user_message)
        queries = self._extract_queries(response)
        if not queries:
            return state.model_copy(update={"status_rows": None})
        status_rows = self._run_queries(queries)
        return state.model_copy(update={"status_rows": status_rows})

    def _build_chain(self):
        """Create the prompt-to-structured-output chain."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required to query status.")
        llm = ChatOpenAI(
            model=DEFAULT_MODEL,
            api_key=api_key,
            max_tokens=256,
        )
        llm_with_structure = llm.with_structured_output(QueryStatusResponse)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT),
                ("human", "{user_message}"),
            ]
        )
        return prompt | llm_with_structure

    def _invoke_llm(self, chain, user_message: str):
        """Invoke the LLM chain with the user message."""
        return chain.invoke({"user_message": user_message})

    def _extract_queries(self, response) -> list[str] | None:
        """Extract query list from LLM response."""
        if isinstance(response, QueryStatusResponse):
            return response.queries
        if isinstance(response, dict):
            return response.get("queries")
        return getattr(response, "queries", None)

    def _run_queries(self, queries: list[str]) -> list[dict]:
        """Execute SQL queries and return combined rows."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logging.warning("DATABASE_URL not set; skipping status query")
            return []

        rows: list[dict] = []
        with psycopg.connect(database_url) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                for query in queries:
                    if not query or not query.strip().lower().startswith("select"):
                        logging.warning("Skipping non-SELECT query: %s", query)
                        continue
                    cur.execute(query)
                    rows.extend(cur.fetchall())
        return rows
