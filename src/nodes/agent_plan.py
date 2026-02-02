import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.agent_plan import AgentPlanResponse
from src.schemas.state import WorkflowState


class AgentPlan:
    """Plan the next workflow action based on user input and state."""

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
        logging.info("AgentPlan input state=%s", state)
        return self._plan(state)

    def _plan(self, state: WorkflowState) -> WorkflowState:
        """Determine the next action for the workflow."""
        formatted_state = self._format_state(state)
        response = self._invoke_llm(formatted_state)
        return state.model_copy(update={"next_action": response.next_action})

    def _load_prompt(self) -> str:
        """Load the agent plan prompt text from disk."""
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "agent_plan.md"
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
        return prompt | llm.with_structured_output(AgentPlanResponse)

    def _format_state(self, state: WorkflowState) -> str:
        """Format the workflow state for the prompt."""
        payload = {
            "user_input": state.user_input,
            "file_id": state.file_id,
            "receipt_json_present": state.receipt_json is not None,
            "expense_id": state.expense_id,
            "status_rows_present": state.status_rows is not None,
            "status_rows_count": len(state.status_rows) if state.status_rows else 0,
        }
        return json.dumps(payload, ensure_ascii=False)

    def _invoke_llm(self, formatted_state: str) -> AgentPlanResponse:
        """Invoke the LLM chain and return the structured response."""
        return self._chain.invoke({"state_json": formatted_state})
