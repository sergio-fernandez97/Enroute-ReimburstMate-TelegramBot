"""LangGraph workflow wiring for the ReimburstMate bot."""
import logging
from typing import Literal

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from src.nodes import AgentPlan, ExtractReceipt, QueryStatus, RenderAndPost, UpsertExpense
from src.schemas.state import WorkflowState


def _route_next_step(
    state: WorkflowState,
) -> Literal["extract_receipt", "upsert_expense", "query_status", "render_and_post", END]:
    """Route execution based on the workflow state's next_action hint."""
    logging.info("Routing from AgentPlan with next_action=%s", state.next_action)

    routes = {
        "extract_receipt": "extract_receipt",
        "upsert_expense": "upsert_expense",
        "query_status": "query_status",
        "render_and_post": "render_and_post",
    }

    return routes.get(state.next_action, END)


def build_graph() -> StateGraph:
    """Build the LangGraph workflow for the Telegram bot."""
    builder = StateGraph(WorkflowState)

    builder.add_node("agent_plan", AgentPlan())
    builder.add_node("extract_receipt", ExtractReceipt())
    builder.add_node("upsert_expense", UpsertExpense())
    builder.add_node("query_status", QueryStatus())
    builder.add_node("render_and_post", RenderAndPost())

    builder.add_edge(START, "agent_plan")
    builder.add_conditional_edges("agent_plan", _route_next_step)

    builder.add_edge("extract_receipt", "agent_plan")
    builder.add_edge("upsert_expense", "agent_plan")
    builder.add_edge("query_status", "agent_plan")
    builder.add_edge("render_and_post", END)

    return builder.compile()


graph = build_graph()
