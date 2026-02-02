import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.post_and_render import RenderAndPostResponse
from src.schemas.state import WorkflowState


class RenderAndPost:
    """Render a user-facing response and prepare it for posting."""

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
        logging.info("RenderAndPost input state=%s", state)
        return self._render(state)

    def _render(self, state: WorkflowState) -> WorkflowState:
        """Render a user-facing response from the workflow state."""
        formatted_state = self._format_state(state)
        response = self._invoke_llm(formatted_state)
        return state.model_copy(update={"response_text": response.response_text})

    def _load_prompt(self) -> str:
        """Load the render prompt text from disk."""
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "post_and_render.md"
        return prompt_path.read_text(encoding="utf-8").strip()

    def _build_chain(self):
        """Build the prompt -> LLM chain with structured output."""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._prompt_text),
                ("human", "Current workflow state:\n{state_json}"),
            ]
        )
        llm = ChatOpenAI(model=self._model)
        return prompt | llm.with_structured_output(RenderAndPostResponse)

    def _format_state(self, state: WorkflowState) -> str:
        """Format the workflow state for the prompt."""
        payload = state.model_dump()
        return json.dumps(payload, ensure_ascii=False, default=str)

    def _invoke_llm(self, formatted_state: str) -> RenderAndPostResponse:
        """Invoke the LLM chain and return the structured response."""
        return self._chain.invoke({"state_json": formatted_state})
