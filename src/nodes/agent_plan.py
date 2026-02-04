import json
import logging
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.agent_plan import AgentPlanResponse
from src.schemas.state import WorkflowState


class AgentPlan:
    """Routes workflow execution based on the user input and state."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        """Initialize the planning node.

        Args:
            model: OpenAI model name for planning.
        """
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "agent_plan.md"
        self._prompt = prompt_path.read_text(encoding="utf-8").strip()
        self._llm = ChatOpenAI(model=model, temperature=0)

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("AgentPlan input state=%s", state)
        return self._plan(state)

    def _plan(self, state: WorkflowState) -> WorkflowState:
        """Create the next action plan using structured output."""
        formatted_state = self._format_state(state)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._prompt),
                ("human", "Current workflow state:\n{state}"),
            ]
        )
        chain = prompt | self._llm.with_structured_output(AgentPlanResponse)
        response = chain.invoke({"state": formatted_state})

        logging.info("AgentPlan next_action=%s", response.next_action)
        return state.model_copy(update={"next_action": response.next_action})

    @staticmethod
    def _format_state(state: WorkflowState) -> str:
        """Format the workflow state for prompt consumption."""
        payload = {key: value for key, value in state.model_dump().items() if value is not None}
        return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
