import unittest
from unittest.mock import patch

from src.nodes.query_status import QueryStatus
from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState


class TestQueryStatus(unittest.TestCase):
    def test_query_status_populates_status_rows(self) -> None:
        with patch("src.nodes.query_status.QueryStatus._build_chain", return_value=object()):
            node = QueryStatus()

        with patch.object(
            node,
            "_invoke_llm",
            return_value=QueryStatusResponse(queries=["SELECT 1 AS id"]),
        ):
            with patch.object(node, "_execute_queries", return_value=[{"id": 1}]):
                state = WorkflowState(user_input="Show my status")
                updated = node(state)

        self.assertEqual(updated.status_rows, [{"id": 1}])

    def test_query_status_skips_when_no_queries(self) -> None:
        with patch("src.nodes.query_status.QueryStatus._build_chain", return_value=object()):
            node = QueryStatus()

        with patch.object(
            node,
            "_invoke_llm",
            return_value=QueryStatusResponse(queries=None),
        ):
            with patch.object(node, "_execute_queries") as mock_execute:
                state = WorkflowState(user_input="Show my status")
                updated = node(state)

        self.assertIsNone(updated.status_rows)
        mock_execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
