import unittest
from unittest.mock import patch

from src.nodes.agent_plan import AgentPlan
from src.schemas.agent_plan import AgentPlanResponse
from src.schemas.state import WorkflowState


class _FakeChain:
    def __init__(self, response: AgentPlanResponse) -> None:
        self._response = response

    def invoke(self, _inputs: dict) -> AgentPlanResponse:
        return self._response


class _FakePrompt:
    def __init__(self, response: AgentPlanResponse) -> None:
        self._response = response

    def __or__(self, _other: object) -> _FakeChain:
        return _FakeChain(self._response)


class _FakeLLM:
    def with_structured_output(self, _schema: object) -> object:
        return object()


class AgentPlanTests(unittest.TestCase):
    def test_agent_plan_updates_next_action(self) -> None:
        response = AgentPlanResponse(next_action="query_status")
        state = WorkflowState(user_input="Check status")

        with patch(
            "src.nodes.agent_plan.ChatPromptTemplate.from_messages",
            return_value=_FakePrompt(response),
        ):
            with patch.object(AgentPlan, "_get_llm", return_value=_FakeLLM()):
                updated_state = AgentPlan()(state)

        self.assertIsNone(state.next_action)
        self.assertEqual(updated_state.next_action, "query_status")


if __name__ == "__main__":
    unittest.main()
