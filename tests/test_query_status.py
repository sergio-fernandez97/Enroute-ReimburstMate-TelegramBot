import unittest
from unittest.mock import patch

from src.nodes.query_status import QueryStatus
from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState


class _FakeChain:
    def __init__(self, response: QueryStatusResponse) -> None:
        self._response = response

    def invoke(self, _inputs: dict) -> QueryStatusResponse:
        return self._response


class _FakePrompt:
    def __init__(self, response: QueryStatusResponse) -> None:
        self._response = response

    def __or__(self, _other: object) -> _FakeChain:
        return _FakeChain(self._response)


class _FakeLLM:
    def with_structured_output(self, _schema: object) -> object:
        return object()


class QueryStatusTests(unittest.TestCase):
    def test_query_status_updates_rows(self) -> None:
        response = QueryStatusResponse(queries=["SELECT 1"])
        state = WorkflowState(user_input="Show my status")
        rows = [{"status": "approved"}]

        with patch(
            "src.nodes.query_status.ChatPromptTemplate.from_messages",
            return_value=_FakePrompt(response),
        ):
            with patch.object(QueryStatus, "_get_llm", return_value=_FakeLLM()):
                with patch.object(
                    QueryStatus, "_fetch_status_rows", return_value=rows
                ) as fetch_rows:
                    updated_state = QueryStatus()(state)

        fetch_rows.assert_called_once_with(response.queries)
        self.assertIsNone(state.status_rows)
        self.assertEqual(updated_state.status_rows, rows)

    def test_query_status_no_queries(self) -> None:
        response = QueryStatusResponse(queries=None)
        state = WorkflowState(user_input="Show my status")

        with patch(
            "src.nodes.query_status.ChatPromptTemplate.from_messages",
            return_value=_FakePrompt(response),
        ):
            with patch.object(QueryStatus, "_get_llm", return_value=_FakeLLM()):
                with patch.object(QueryStatus, "_fetch_status_rows") as fetch_rows:
                    updated_state = QueryStatus()(state)

        fetch_rows.assert_not_called()
        self.assertIsNone(updated_state.status_rows)


if __name__ == "__main__":
    unittest.main()
