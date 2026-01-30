import logging
from typing import Any, Dict

from src.schemas.state import WorkflowState


class UpsertExpense:
    """Creates or updates an expense record in the system of record."""

    def __call__(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.
            config: Node configuration.

        Returns:
            Updated workflow state.
        """
        logging.info("UpsertExpense input state=%s", state)
        return self._upsert(state, config)

    def _upsert(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """Placeholder for upsert logic."""
        return state
