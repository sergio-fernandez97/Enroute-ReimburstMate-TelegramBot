import unittest
from unittest.mock import patch

from src.nodes.render_and_post import RenderAndPost
from src.schemas.post_and_render import RenderAndPostResponse
from src.schemas.state import WorkflowState


class DummyChain:
    """Simple chain stub for unit tests."""

    def __init__(self, response):
        self._response = response

    def invoke(self, _inputs):
        return self._response


class TestRenderAndPost(unittest.TestCase):
    def test_render_updates_state_with_structured_response(self):
        state = WorkflowState(user_input="Submit receipt", expense_id="EXP-123")
        node = RenderAndPost()
        dummy_chain = DummyChain(
            RenderAndPostResponse(response_text="Submitted EXP-123.")
        )

        with patch.object(RenderAndPost, "_build_chain", return_value=dummy_chain):
            result = node(state)

        self.assertEqual(result.response_text, "Submitted EXP-123.")

    def test_render_updates_state_with_dict_response(self):
        state = WorkflowState(user_input="Check status", status_rows=[])
        node = RenderAndPost()
        dummy_chain = DummyChain({"response_text": "No expenses found."})

        with patch.object(RenderAndPost, "_build_chain", return_value=dummy_chain):
            result = node(state)

        self.assertEqual(result.response_text, "No expenses found.")


if __name__ == "__main__":
    unittest.main()
