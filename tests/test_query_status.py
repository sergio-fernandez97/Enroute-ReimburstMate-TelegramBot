import unittest
from unittest.mock import patch

from src.nodes.query_status import QueryStatus
from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState


class DummyChain:
    """Simple chain stub for unit tests."""

    def __init__(self, response):
        self._response = response

    def invoke(self, _inputs):
        return self._response


class TestQueryStatus(unittest.TestCase):
    def test_query_status_returns_none_when_no_queries(self):
        state = WorkflowState(user_input="Status update please")
        node = QueryStatus()
        dummy_chain = DummyChain(QueryStatusResponse(queries=None))

        with patch.object(QueryStatus, "_build_chain", return_value=dummy_chain):
            result = node(state)

        self.assertIsNone(result.status_rows)

    def test_query_status_runs_queries_and_updates_state(self):
        state = WorkflowState(user_input="Show my latest expenses")
        node = QueryStatus()
        dummy_chain = DummyChain(
            QueryStatusResponse(queries=["SELECT 1 AS id"])
        )
        fake_rows = [{"id": 1}]

        with patch.object(QueryStatus, "_build_chain", return_value=dummy_chain):
            with patch.object(QueryStatus, "_run_queries", return_value=fake_rows):
                result = node(state)

        self.assertEqual(result.status_rows, fake_rows)


if __name__ == "__main__":
    unittest.main()
