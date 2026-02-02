import json
import unittest
from unittest.mock import patch

from src.nodes.render_and_post import RenderAndPost
from src.schemas.post_and_render import RenderAndPostResponse
from src.schemas.state import WorkflowState


class TestRenderAndPost(unittest.TestCase):
    def test_render_and_post_updates_response_text(self) -> None:
        with patch("src.nodes.render_and_post.RenderAndPost._build_chain", return_value=object()):
            renderer = RenderAndPost()

        with patch.object(
            renderer,
            "_invoke_llm",
            return_value=RenderAndPostResponse(response_text="All set!"),
        ):
            state = WorkflowState(user_input="Confirm")
            updated = renderer(state)

        self.assertEqual(updated.response_text, "All set!")

    def test_render_and_post_formats_state(self) -> None:
        with patch("src.nodes.render_and_post.RenderAndPost._build_chain", return_value=object()):
            renderer = RenderAndPost()

        state = WorkflowState(
            user_input="Status",
            status_rows=[{"created_at": object()}],
        )

        formatted = renderer._format_state(state)
        payload = json.loads(formatted)

        self.assertEqual(payload["user_input"], "Status")
        self.assertIsInstance(payload["status_rows"][0]["created_at"], str)


if __name__ == "__main__":
    unittest.main()
