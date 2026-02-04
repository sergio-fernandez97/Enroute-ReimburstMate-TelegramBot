import unittest

from src.nodes.query_status import QueryStatus
from src.schemas.query_status import QueryStatusResponse
from src.schemas.state import WorkflowState


class _FakeLLM:
    def __init__(self, response: QueryStatusResponse) -> None:
        self._response = response
        self.last_payload: dict | None = None
        self.schema = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self

    def invoke(self, payload):
        self.last_payload = payload
        return self._response


class QueryStatusTests(unittest.TestCase):
    def test_no_queries_keeps_status_rows_none(self) -> None:
        llm = _FakeLLM(QueryStatusResponse(queries=None))
        node = QueryStatus(llm=llm, database_url="")
        state = WorkflowState(user_input="status please")

        updated = node(state)

        self.assertIsNone(updated.status_rows)
        self.assertEqual(llm.last_payload.get("user_input"), state.user_input)

    def test_queries_without_db_returns_empty_rows(self) -> None:
        llm = _FakeLLM(QueryStatusResponse(queries=["SELECT 1;"]))
        node = QueryStatus(llm=llm, database_url="")
        state = WorkflowState(user_input="latest expenses")

        updated = node(state)

        self.assertEqual(updated.status_rows, [])


if __name__ == "__main__":
    unittest.main()
