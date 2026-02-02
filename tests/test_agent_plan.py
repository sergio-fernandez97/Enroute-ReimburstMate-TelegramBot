import json
import unittest
from unittest.mock import patch

from src.nodes.agent_plan import AgentPlan
from src.schemas.agent_plan import AgentPlanResponse
from src.schemas.state import WorkflowState


class TestAgentPlan(unittest.TestCase):
    def test_agent_plan_updates_next_action(self) -> None:
        with patch("src.nodes.agent_plan.AgentPlan._build_chain", return_value=object()):
            planner = AgentPlan()

        with patch.object(
            planner,
            "_invoke_llm",
            return_value=AgentPlanResponse(next_action="query_status"),
        ):
            state = WorkflowState(user_input="Show my history")
            updated = planner(state)

        self.assertEqual(updated.next_action, "query_status")

    def test_agent_plan_formats_state(self) -> None:
        with patch("src.nodes.agent_plan.AgentPlan._build_chain", return_value=object()):
            planner = AgentPlan()

        state = WorkflowState(
            user_input="Upload",
            file_id="file_123",
            receipt_json=None,
            expense_id=None,
            status_rows=[{"id": 1}],
        )

        formatted = planner._format_state(state)
        payload = json.loads(formatted)

        self.assertEqual(payload["user_input"], "Upload")
        self.assertEqual(payload["file_id"], "file_123")
        self.assertFalse(payload["receipt_json_present"])
        self.assertTrue(payload["status_rows_present"])
        self.assertEqual(payload["status_rows_count"], 1)


if __name__ == "__main__":
    unittest.main()
