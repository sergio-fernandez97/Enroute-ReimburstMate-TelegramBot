import json
import logging
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.post_and_render import RenderAndPostResponse
from src.schemas.state import WorkflowState


class RenderAndPost:
    """Renders the final response and posts it to Telegram."""

    def __init__(self, model: str = "gpt-4o-mini", llm: ChatOpenAI | None = None) -> None:
        """Initialize the render and post node.

        Args:
            model: OpenAI model name for response rendering.
            llm: Optional LLM client override for testing.
        """
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "post_and_render.md"
        self._prompt = prompt_path.read_text(encoding="utf-8").strip()
        self._llm = llm or ChatOpenAI(model=model, temperature=0)

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
        """Render the final response using structured output."""
        formatted_state = self._format_state(state)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._prompt),
                ("human", "Current workflow state:\n{state}"),
            ]
        )
        chain = prompt | self._llm.with_structured_output(RenderAndPostResponse)
        response = chain.invoke({"state": formatted_state})
        return state.model_copy(update={"response_text": response.response_text})

    @staticmethod
    def _format_state(state: WorkflowState) -> str:
        """Format the workflow state for prompt consumption."""
        payload = {key: value for key, value in state.model_dump().items() if value is not None}
        return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
