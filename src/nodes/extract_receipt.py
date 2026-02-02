import logging
from typing import Any, Dict

from src.schemas.state import WorkflowState


class ExtractReceipt:
    """Extracts structured data from receipt images."""

    def __call__(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.
            config: Node configuration.

        Returns:
            Updated workflow state.
        """
        logging.info("ExtractReceipt input state=%s", state)
        return self._extract(state, config)

    def _extract(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """Placeholder for receipt extraction logic."""
        return state
