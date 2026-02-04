import json
import logging
import os
from pathlib import Path
from typing import Any

import psycopg
from langchain_openai import ChatOpenAI

from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "query_status.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()


class QueryStatusNode:
    """Query expense status for the user."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("QueryStatusNode input state=%s", state)
        return self._run(state)

    def _run(self, state: WorkflowState) -> WorkflowState:
        """Generate status queries, run them, and update the workflow state."""
        prompt = self._build_prompt(state)
        llm = self._get_llm()
        llm_with_structure = llm.with_structured_output(QueryStatusResponse)
        result = llm_with_structure.invoke(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
        queries = result.queries
        if queries is None:
            return state

        status_rows = self._run_queries(queries)
        return state.model_copy(update={"status_rows": status_rows})

    def _build_prompt(self, state: WorkflowState) -> str:
        """Format prompt with user context and the user message."""
        user_context = {
            "telegram_user_id": state.telegram_user_id,
            "username": state.username,
            "first_name": state.first_name,
            "last_name": state.last_name,
        }
        context_payload = json.dumps(user_context, indent=2, default=str)
        user_message = state.user_input or ""
        return (
            f"{PROMPT}\n\nUser context:\n{context_payload}\n\nUser message:\n{user_message}"
        )

    def _get_llm(self) -> ChatOpenAI:
        """Create the LLM instance used for status query generation."""
        model = os.getenv("QUERY_STATUS_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model)

    def _run_queries(self, queries: list[str]) -> list[dict[str, Any]]:
        """Execute SELECT queries and return rows as dicts."""
        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            logging.warning(
                "QueryStatusNode missing DATABASE_URL; returning empty status rows."
            )
            return []

        rows: list[dict[str, Any]] = []
        try:
            with psycopg.connect(database_url) as conn:
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    for query in queries:
                        if not self._is_select_query(query):
                            logging.warning("Skipping non-SELECT query: %s", query)
                            continue
                        cur.execute(query)
                        rows.extend(cur.fetchall())
        except Exception:
            logging.exception("QueryStatusNode failed to run status queries")
            return []
        return rows

    def _is_select_query(self, query: str) -> bool:
        """Return True if the query begins with SELECT after trimming."""
        return query.strip().lower().startswith("select")
