import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.schemas.agent_plan import AgentPlanResponse
from src.schemas.state import WorkflowState

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent_plan.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()


class AgentPlan:
    """Plans the next action based on the user input and current state."""

    def __call__(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.
            config: Node configuration.

        Returns:
            Updated workflow state.
        """
        logging.info("AgentPlan input state=%s", state)
        return self._plan(state, config)

    def _plan(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """Plan the next action using an LLM with structured output."""
        formatted_state = self._format_state_for_prompt(state)
        llm = self._get_llm(config)
        llm_with_structure = llm.with_structured_output(AgentPlanResponse)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT),
                ("human", "State:\n{state_json}"),
            ]
        )
        chain = prompt | llm_with_structure
        result = chain.invoke({"state_json": formatted_state})

        logging.info("AgentPlan selected next_action=%s", result.next_action)
        return state.model_copy(update={"next_action": result.next_action})

    def _get_llm(self, config: Dict[str, Any]) -> ChatOpenAI:
        """Create the chat model for planning."""
        model = config.get("model", "gpt-4o-mini")
        api_key = os.environ.get("OPENAI_API_KEY")
        return ChatOpenAI(model=model, api_key=api_key)

    def _format_state_for_prompt(self, state: WorkflowState) -> str:
        """Format the workflow state for prompt consumption."""
        payload = {
            "user_input": state.user_input,
            "telegram_user_id": state.telegram_user_id,
            "file_id": state.file_id,
            "receipt_json_present": state.receipt_json is not None,
            "expense_id": state.expense_id,
            "status_rows_count": len(state.status_rows or []),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)
