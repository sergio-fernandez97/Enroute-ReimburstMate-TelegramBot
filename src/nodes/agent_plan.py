import logging
from typing import Any, Dict

from src.schemas.state import WorkflowState


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
        """Placeholder for planning logic."""
        return state
