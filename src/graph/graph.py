from __future__ import annotations

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


def _route_from_agent_plan(state: WorkflowState) -> str:
    """Route to the next node based on the agent plan."""
    if state.next_action == EXTRACT_RECEIPT_NODE:
        return EXTRACT_RECEIPT_NODE
    if state.next_action == UPSERT_EXPENSE_NODE:
        return UPSERT_EXPENSE_NODE
    if state.next_action == QUERY_STATUS_NODE:
        return QUERY_STATUS_NODE
    if state.next_action == RENDER_AND_POST_NODE:
        return RENDER_AND_POST_NODE
    return "__end__"


graph = StateGraph(WorkflowState)

graph.add_node(AGENT_PLAN_NODE, AgentPlan())
graph.add_node(EXTRACT_RECEIPT_NODE, ExtractReceipt())
graph.add_node(UPSERT_EXPENSE_NODE, UpsertExpense())
graph.add_node(QUERY_STATUS_NODE, QueryStatus())
graph.add_node(RENDER_AND_POST_NODE, RenderAndPost())

graph.add_edge(START, AGENT_PLAN_NODE)
graph.add_conditional_edges(
    AGENT_PLAN_NODE,
    _route_from_agent_plan,
    {
        EXTRACT_RECEIPT_NODE: EXTRACT_RECEIPT_NODE,
        UPSERT_EXPENSE_NODE: UPSERT_EXPENSE_NODE,
        QUERY_STATUS_NODE: QUERY_STATUS_NODE,
        RENDER_AND_POST_NODE: RENDER_AND_POST_NODE,
        "__end__": END,
    },
)

graph.add_edge(EXTRACT_RECEIPT_NODE, AGENT_PLAN_NODE)
graph.add_edge(UPSERT_EXPENSE_NODE, AGENT_PLAN_NODE)
graph.add_edge(QUERY_STATUS_NODE, AGENT_PLAN_NODE)
graph.add_edge(RENDER_AND_POST_NODE, END)


def build_graph():
    """Create the LangGraph workflow for the ReimburseMate bot."""
    return graph.compile()
