import json
import logging
import os
from pathlib import Path
from typing import Any, Iterable, List

import psycopg
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from psycopg.rows import dict_row

from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "query_status.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()


class QueryStatus:
    """Queries expense status and history."""

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
        """Query status data using an LLM-generated query plan."""
        formatted_state = self._format_state_for_prompt(state)
        llm = self._get_llm()
        llm_with_structure = llm.with_structured_output(QueryStatusResponse)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT),
                ("human", "User message:\n{user_input}\n\nState:\n{state_json}"),
            ]
        )
        chain = prompt | llm_with_structure
        result = chain.invoke(
            {
                "user_input": state.user_input or "",
                "state_json": formatted_state,
            }
        )

        if not result.queries:
            logging.info("QueryStatus did not produce queries.")
            return state

        status_rows = self._fetch_status_rows(result.queries)
        logging.info("QueryStatus retrieved %s rows.", len(status_rows))
        return state.model_copy(update={"status_rows": status_rows})

    def _get_llm(self) -> ChatOpenAI:
        """Create the chat model for query generation."""
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        api_key = os.environ.get("OPENAI_API_KEY")
        return ChatOpenAI(model=model, api_key=api_key)

    def _format_state_for_prompt(self, state: WorkflowState) -> str:
        """Format the workflow state for prompt consumption."""
        payload = {
            "user_input": state.user_input,
            "telegram_user_id": state.telegram_user_id,
            "username": state.username,
            "first_name": state.first_name,
            "last_name": state.last_name,
            "expense_id": state.expense_id,
            "status_rows_count": len(state.status_rows or []),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _fetch_status_rows(self, queries: Iterable[str]) -> List[dict[str, Any]]:
        """Execute query list and collect rows for response building."""
        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            logging.warning("DATABASE_URL not set; skipping status query.")
            return []

        rows: List[dict[str, Any]] = []
        with psycopg.connect(database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                for query in queries:
                    if not query:
                        continue
                    normalized_query = self._normalize_query(query)
                    if not self._is_select_query(normalized_query):
                        logging.warning("QueryStatus skipped non-SQL query=%s", query)
                        continue
                    cur.execute(normalized_query)
                    if cur.description:
                        rows.extend(cur.fetchall())
        return rows

    def _normalize_query(self, query: str) -> str:
        """Strip optional language prefixes so only SQL is executed."""
        cleaned = query.strip()
        lowered = cleaned.lower()
        for prefix in ("sql:", "postgresql:", "sql/postgresql:"):
            if lowered.startswith(prefix):
                return cleaned[len(prefix) :].strip()
        return cleaned

    def _is_select_query(self, query: str) -> bool:
        """Ensure only read-only SQL is executed."""
        lowered = query.strip().lower()
        return lowered.startswith("select") or lowered.startswith("with")
