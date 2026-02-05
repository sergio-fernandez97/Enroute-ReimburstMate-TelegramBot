import unittest
from unittest.mock import patch

from src.nodes.agent_plan import AgentPlan
from src.schemas.agent_plan import AgentPlanResponse
from src.schemas.state import WorkflowState


class DummyChain:
    """Simple chain stub for unit tests."""

    def __init__(self, response):
        self._response = response

    def invoke(self, _inputs):
        return self._response


class TestAgentPlan(unittest.TestCase):
    def test_plan_updates_state_with_structured_response(self):
        state = WorkflowState(user_input="Hello")
        node = AgentPlan()
        dummy_chain = DummyChain(
            AgentPlanResponse(next_action="render_and_post")
        )

        with patch.object(AgentPlan, "_build_chain", return_value=dummy_chain):
            result = node(state)

        self.assertEqual(result.next_action, "render_and_post")

    def test_plan_updates_state_with_dict_response(self):
        state = WorkflowState(user_input="Status please", file_id="file-123")
        node = AgentPlan()
        dummy_chain = DummyChain({"next_action": "extract_receipt"})

        with patch.object(AgentPlan, "_build_chain", return_value=dummy_chain):
            result = node(state)

        self.assertEqual(result.next_action, "extract_receipt")


if __name__ == "__main__":
    unittest.main()
