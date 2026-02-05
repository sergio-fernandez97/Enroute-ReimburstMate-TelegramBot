import json
import logging
import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.agent_plan import AgentPlanResponse
from src.schemas.state import WorkflowState

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent_plan.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()
DEFAULT_MODEL = "gpt-4o-mini"


class AgentPlan:
    """Plan the next workflow action based on current state."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("AgentPlan input state=%s", state)
        return self._plan_next_action(state)

    def _plan_next_action(self, state: WorkflowState) -> WorkflowState:
        """Select the next action to run in the workflow."""
        chain = self._build_chain()
        state_summary = self._format_state_for_prompt(state)
        response = chain.invoke({"state_summary": state_summary})
        next_action = self._extract_next_action(response)
        return state.model_copy(update={"next_action": next_action})

    def _build_chain(self):
        """Create the prompt-to-structured-output chain."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required to plan next actions.")
        llm = ChatOpenAI(
            model=DEFAULT_MODEL,
            api_key=api_key,
            max_tokens=256,
        )
        llm_with_structure = llm.with_structured_output(AgentPlanResponse)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT),
                ("human", "{state_summary}"),
            ]
        )
        return prompt | llm_with_structure

    def _format_state_for_prompt(self, state: WorkflowState) -> str:
        """Format workflow state into a prompt-friendly summary."""
        state_payload = {
            "user_input": state.user_input,
            "file_id": state.file_id,
            "receipt_json_present": state.receipt_json is not None,
            "receipt_json_keys": (
                sorted(state.receipt_json.keys())
                if isinstance(state.receipt_json, dict)
                else None
            ),
            "expense_id": state.expense_id,
            "status_rows_present": state.status_rows is not None,
            "status_rows_count": len(state.status_rows) if state.status_rows else 0,
            "next_action": state.next_action,
            "telegram_user_id": state.telegram_user_id,
        }
        return (
            "Current workflow state (JSON):\n"
            f"{json.dumps(state_payload, indent=2, ensure_ascii=True)}"
        )

    def _extract_next_action(self, response: AgentPlanResponse) -> str:
        """Extract the next_action value from the LLM response."""
        if isinstance(response, AgentPlanResponse):
            return response.next_action
        if isinstance(response, dict):
            return response.get("next_action")
        return getattr(response, "next_action", None)
