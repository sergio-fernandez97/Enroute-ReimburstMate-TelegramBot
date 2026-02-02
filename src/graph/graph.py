from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from src.nodes.agent_plan import AgentPlan
from src.nodes.extract_receipt import ExtractReceipt
from src.nodes.query_status import QueryStatus
from src.nodes.render_and_post import RenderAndPost
from src.nodes.upsert_expense import UpsertExpense
from src.schemas.state import WorkflowState

AGENT_PLAN_NODE = "agent_plan"
EXTRACT_RECEIPT_NODE = "extract_receipt"
UPSERT_EXPENSE_NODE = "upsert_expense"
QUERY_STATUS_NODE = "query_status"
RENDER_AND_POST_NODE = "render_and_post"


def _route_next_action(state: WorkflowState) -> str:
    """Route from the planner to the requested next action."""
    if not state.next_action:
        return RENDER_AND_POST_NODE
    return state.next_action


def build_graph() -> Any:
    """Build the LangGraph workflow for the ReimburstMate bot."""
    builder = StateGraph(WorkflowState)

    builder.add_node(AGENT_PLAN_NODE, AgentPlan())
    builder.add_node(EXTRACT_RECEIPT_NODE, ExtractReceipt())
    builder.add_node(UPSERT_EXPENSE_NODE, UpsertExpense())
    builder.add_node(QUERY_STATUS_NODE, QueryStatus())
    builder.add_node(RENDER_AND_POST_NODE, RenderAndPost())

    builder.add_edge(START, AGENT_PLAN_NODE)
    builder.add_conditional_edges(
        AGENT_PLAN_NODE,
        _route_next_action,
        {
            EXTRACT_RECEIPT_NODE: EXTRACT_RECEIPT_NODE,
            UPSERT_EXPENSE_NODE: UPSERT_EXPENSE_NODE,
            QUERY_STATUS_NODE: QUERY_STATUS_NODE,
            RENDER_AND_POST_NODE: RENDER_AND_POST_NODE,
        },
    )

    builder.add_edge(EXTRACT_RECEIPT_NODE, AGENT_PLAN_NODE)
    builder.add_edge(UPSERT_EXPENSE_NODE, AGENT_PLAN_NODE)
    builder.add_edge(QUERY_STATUS_NODE, AGENT_PLAN_NODE)
    builder.add_edge(RENDER_AND_POST_NODE, END)

    return builder.compile()


graph = build_graph()
