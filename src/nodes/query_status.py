import logging
from typing import Any, Dict

from src.schemas.state import WorkflowState


class QueryStatus:
    """Queries expense status and history."""

    def __call__(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.
            config: Node configuration.

        Returns:
            Updated workflow state.
        """
        logging.info("QueryStatus input state=%s", state)
        return self._query(state, config)

    def _query(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """Placeholder for query logic."""
        return state
