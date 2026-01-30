from langgraph.graph import END, StateGraph

from src.nodes.agent_plan import AgentPlan
from src.nodes.extract_receipt import ExtractReceipt
from src.nodes.query_status import QueryStatus
from src.nodes.render_and_post import RenderAndPost
from src.nodes.upsert_expense import UpsertExpense
from src.schemas.state import WorkflowState


def route_from_agent_plan(state: WorkflowState) -> str:
    """Return the next node name chosen by the agent plan."""
    return state.next_action or "render_and_post"


def build_graph() -> StateGraph:
    """Build the LangGraph workflow."""
    graph = StateGraph(WorkflowState)

    graph.add_node("agent_plan", AgentPlan())
    graph.add_node("extract_receipt", ExtractReceipt())
    graph.add_node("upsert_expense", UpsertExpense())
    graph.add_node("query_status", QueryStatus())
    graph.add_node("render_and_post", RenderAndPost())

    graph.set_entry_point("agent_plan")

    graph.add_conditional_edges(
        "agent_plan",
        route_from_agent_plan,
        {
            "extract_receipt": "extract_receipt",
            "upsert_expense": "upsert_expense",
            "query_status": "query_status",
            "render_and_post": "render_and_post",
        },
    )

    graph.add_edge("extract_receipt", "agent_plan")
    graph.add_edge("upsert_expense", "agent_plan")
    graph.add_edge("query_status", "agent_plan")
    graph.add_edge("render_and_post", END)

    return graph


graph = build_graph()
