import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.post_and_render import RenderAndPostResponse
from src.schemas.state import WorkflowState

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "post_and_render.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()


class RenderAndPost:
    """Renders a response and posts it back to the user."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("RenderAndPost input state=%s", state)
        return self._render(state)

    def _render(self, state: WorkflowState) -> WorkflowState:
        """Render the response using an LLM with structured output."""
        formatted_state = self._format_state_for_prompt(state)
        llm = self._get_llm()
        llm_with_structure = llm.with_structured_output(RenderAndPostResponse)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT),
                ("human", "State:\n{state_json}"),
            ]
        )
        chain = prompt | llm_with_structure
        result = chain.invoke({"state_json": formatted_state})

        logging.info("RenderAndPost response_text length=%s", len(result.response_text))
        return state.model_copy(update={"response_text": result.response_text})

    def _get_llm(self) -> ChatOpenAI:
        """Create the chat model for rendering."""
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        api_key = os.environ.get("OPENAI_API_KEY")
        return ChatOpenAI(model=model, api_key=api_key)

    def _format_state_for_prompt(self, state: WorkflowState) -> str:
        """Format the workflow state for prompt consumption."""
        payload = state.model_dump()
        return json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            default=self._json_default,
        )

    def _json_default(self, value: object) -> str | list[object]:
        """Coerce non-JSON types into prompt-safe representations."""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, set):
            return list(value)
        return str(value)
