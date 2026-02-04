import unittest
from unittest.mock import Mock, patch

from src.nodes.post_and_render import RenderAndPostNode
from src.schemas.state import WorkflowState


class TestPostAndRenderNode(unittest.TestCase):
    def test_updates_response_text(self) -> None:
        node = RenderAndPostNode()
        state = WorkflowState(user_input="hello", expense_id="exp_123")
        fake_result = Mock(response_text="All set.")

        llm = Mock()
        llm.with_structured_output.return_value = Mock(
            invoke=Mock(return_value=fake_result)
        )

        with patch.object(node, "_get_llm", return_value=llm):
            result = node(state)

        self.assertEqual(result.response_text, "All set.")

    def test_build_prompt_includes_state(self) -> None:
        node = RenderAndPostNode()
        state = WorkflowState(user_input="status?", telegram_user_id="42")

        prompt = node._build_prompt(state)

        self.assertIn("Current workflow state:", prompt)
        self.assertIn('"user_input": "status?"', prompt)
        self.assertIn('"telegram_user_id": "42"', prompt)


if __name__ == "__main__":
    unittest.main()
