import json
import logging
import os
from pathlib import Path

from langchain_openai import ChatOpenAI

from src.schemas.post_and_render import RenderAndPostResponse
from src.schemas.state import WorkflowState

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "post_and_render.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()


class RenderAndPostNode:
    """Render response content and post back to the user."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("RenderAndPostNode input state=%s", state)
        return self._run(state)

    def _run(self, state: WorkflowState) -> WorkflowState:
        """Render response text based on the current workflow state."""
        prompt = self._build_prompt(state)
        llm = self._get_llm()
        llm_with_structure = llm.with_structured_output(RenderAndPostResponse)

        result = llm_with_structure.invoke(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
        logging.info("RenderAndPostNode response_text=%s", result.response_text)
        return state.model_copy(update={"response_text": result.response_text})

    def _build_prompt(self, state: WorkflowState) -> str:
        """Format prompt with the current workflow state."""
        state_payload = state.model_dump()
        formatted_state = json.dumps(state_payload, indent=2, default=str)
        return f"{PROMPT}\n\nCurrent workflow state:\n{formatted_state}"

    def _get_llm(self) -> ChatOpenAI:
        """Create the LLM instance for rendering."""
        model = os.getenv("POST_AND_RENDER_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model)
