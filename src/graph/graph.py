from langgraph.graph import END, START, StateGraph

from src.nodes.agent_plan import AgentPlanNode
from src.nodes.extract_receipt import ExtractReceiptNode
from src.nodes.query_status import QueryStatusNode
from src.nodes.post_and_render import RenderAndPostNode
from src.nodes.upsert_expense import UpsertExpenseNode
from src.schemas.state import WorkflowState


def _route_next_action(state: WorkflowState) -> str:
    """Route to the next node based on the current state."""
    return state.next_action or "render_and_post"


def build_graph():
    """Build and compile the LangGraph workflow."""
    builder = StateGraph(WorkflowState)

    builder.add_node("agent_plan", AgentPlanNode())
    builder.add_node("extract_receipt", ExtractReceiptNode())
    builder.add_node("upsert_expense", UpsertExpenseNode())
    builder.add_node("query_status", QueryStatusNode())
    builder.add_node("render_and_post", RenderAndPostNode())

    builder.add_edge(START, "agent_plan")
    builder.add_conditional_edges(
        "agent_plan",
        _route_next_action,
        {
            "extract_receipt": "extract_receipt",
            "upsert_expense": "upsert_expense",
            "query_status": "query_status",
            "render_and_post": "render_and_post",
        },
    )

    builder.add_edge("extract_receipt", "agent_plan")
    builder.add_edge("upsert_expense", "agent_plan")
    builder.add_edge("query_status", "agent_plan")
    builder.add_edge("render_and_post", END)

    return builder.compile()


graph = build_graph()
