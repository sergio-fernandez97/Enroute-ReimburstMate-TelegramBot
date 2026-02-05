import json
import logging
import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.post_and_render import RenderAndPostResponse
from src.schemas.state import WorkflowState

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "post_and_render.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()
DEFAULT_MODEL = "gpt-4o-mini"


class RenderAndPost:
    """Render a user response and post it to Telegram."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("RenderAndPost input state=%s", state)
        return self._render_and_post(state)

    def _render_and_post(self, state: WorkflowState) -> WorkflowState:
        """Prepare response text and perform the post action."""
        chain = self._build_chain()
        state_summary = self._format_state_for_prompt(state)
        response = chain.invoke({"state_summary": state_summary})
        response_text = self._extract_response_text(response)
        return state.model_copy(update={"response_text": response_text})

    def _build_chain(self):
        """Create the prompt-to-structured-output chain."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required to render responses.")
        llm = ChatOpenAI(
            model=DEFAULT_MODEL,
            api_key=api_key,
            max_tokens=256,
        )
        llm_with_structure = llm.with_structured_output(RenderAndPostResponse)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT),
                ("human", "{state_summary}"),
            ]
        )
        return prompt | llm_with_structure

    def _format_state_for_prompt(self, state: WorkflowState) -> str:
        """Format workflow state into a prompt-friendly summary."""
        state_payload = state.model_dump()
        return (
            "Current workflow state (JSON):\n"
            f"{json.dumps(state_payload, indent=2, ensure_ascii=True, default=str)}"
        )

    def _extract_response_text(self, response: RenderAndPostResponse) -> str:
        """Extract the response_text value from the LLM response."""
        if isinstance(response, RenderAndPostResponse):
            return response.response_text
        if isinstance(response, dict):
            return response.get("response_text")
        return getattr(response, "response_text", None)
