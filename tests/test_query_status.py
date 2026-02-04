import unittest
from unittest.mock import patch

from src.nodes.query_status import QueryStatusNode
from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState


class _FakeLLM:
    def __init__(self, response: QueryStatusResponse) -> None:
        self._response = response
        self.last_messages = None

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        self.last_messages = messages
        return self._response


class TestQueryStatusNode(unittest.TestCase):
    def test_updates_status_rows_from_queries(self) -> None:
        node = QueryStatusNode()
        fake_llm = _FakeLLM(QueryStatusResponse(queries=["SELECT 1"]))
        expected_rows = [{"id": 1, "status": "approved"}]

        with patch.object(node, "_get_llm", return_value=fake_llm):
            with patch.object(node, "_run_queries", return_value=expected_rows) as run_queries:
                state = WorkflowState(user_input="show my latest")
                result = node(state)

        run_queries.assert_called_once_with(["SELECT 1"])
        self.assertEqual(result.status_rows, expected_rows)
        self.assertIn("show my latest", fake_llm.last_messages[0]["content"])

    def test_leaves_state_when_queries_none(self) -> None:
        node = QueryStatusNode()
        fake_llm = _FakeLLM(QueryStatusResponse(queries=None))

        with patch.object(node, "_get_llm", return_value=fake_llm):
            with patch.object(node, "_run_queries") as run_queries:
                state = WorkflowState(user_input="hi")
                result = node(state)

        run_queries.assert_not_called()
        self.assertIs(result, state)
        self.assertIsNone(result.status_rows)


if __name__ == "__main__":
    unittest.main()
