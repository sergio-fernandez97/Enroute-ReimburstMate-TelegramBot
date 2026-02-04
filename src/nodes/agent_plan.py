import json
import logging
import os
from pathlib import Path

from langchain_openai import ChatOpenAI

from src.schemas.agent_plan import AgentPlanResponse
from src.schemas.state import WorkflowState

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "agent_plan.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()


class AgentPlanNode:
    """Determine the next workflow action."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("AgentPlanNode input state=%s", state)
        return self._run(state)

    def _run(self, state: WorkflowState) -> WorkflowState:
        """Determine the next action and update the workflow state."""
        prompt = self._build_prompt(state)
        llm = self._get_llm()
        llm_with_structure = llm.with_structured_output(AgentPlanResponse)

        result = llm_with_structure.invoke(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
        logging.info("AgentPlanNode next_action=%s", result.next_action)
        return state.model_copy(update={"next_action": result.next_action})

    def _build_prompt(self, state: WorkflowState) -> str:
        """Format prompt with the current workflow state."""
        state_payload = state.model_dump()
        formatted_state = json.dumps(state_payload, indent=2, default=str)
        return f"{PROMPT}\n\nCurrent workflow state:\n{formatted_state}"

    def _get_llm(self) -> ChatOpenAI:
        """Create the LLM instance for planning."""
        model = os.getenv("AGENT_PLAN_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model)
