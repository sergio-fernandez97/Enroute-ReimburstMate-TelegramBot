from typing import Literal

from pydantic import BaseModel, Field


class AgentPlanResponse(BaseModel):
    """Structured response for agent planning."""

    next_action: Literal[
        "extract_receipt",
        "upsert_expense",
        "query_status",
        "render_and_post",
    ] = Field(description="Next workflow action to take")
