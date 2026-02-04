import unittest
from unittest.mock import patch

from src.nodes.render_and_post import RenderAndPost
from src.schemas.post_and_render import RenderAndPostResponse
from src.schemas.state import WorkflowState


class _DummyChain:
    def __init__(self, response, capture):
        self._response = response
        self._capture = capture

    def invoke(self, payload):
        self._capture["payload"] = payload
        return self._response


class _DummyPrompt:
    def __init__(self, chain):
        self._chain = chain

    def __or__(self, _other):
        return self._chain


class _DummyLLM:
    def with_structured_output(self, _schema):
        return object()


class RenderAndPostTests(unittest.TestCase):
    def test_render_and_post_updates_response_text(self):
        capture = {}
        response = RenderAndPostResponse(response_text="Submission recorded: EXP-123")
        dummy_chain = _DummyChain(response, capture)

        with patch("src.nodes.render_and_post.ChatPromptTemplate") as prompt_template:
            prompt_template.from_messages.return_value = _DummyPrompt(dummy_chain)
            node = RenderAndPost(llm=_DummyLLM())
            state = WorkflowState(user_input="Submit expense", expense_id="EXP-123")

            updated = node(state)

        expected_state = node._format_state(state)
        self.assertEqual(capture["payload"], {"state": expected_state})
        self.assertEqual(updated.response_text, "Submission recorded: EXP-123")

    def test_render_and_post_formats_state_without_nones(self):
        capture = {}
        response = RenderAndPostResponse(response_text="Need amount and date")
        dummy_chain = _DummyChain(response, capture)

        with patch("src.nodes.render_and_post.ChatPromptTemplate") as prompt_template:
            prompt_template.from_messages.return_value = _DummyPrompt(dummy_chain)
            node = RenderAndPost(llm=_DummyLLM())
            state = WorkflowState(user_input="Need help")

            updated = node(state)

        expected_state = node._format_state(state)
        self.assertEqual(capture["payload"], {"state": expected_state})
        self.assertNotIn("expense_id", expected_state)
        self.assertEqual(updated.response_text, "Need amount and date")


if __name__ == "__main__":
    unittest.main()
