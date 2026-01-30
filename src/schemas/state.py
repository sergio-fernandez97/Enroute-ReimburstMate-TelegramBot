from typing import Any
from pydantic import BaseModel, Field

class WorkflowState(BaseModel):
    """Shared workflow state passed between nodes."""

    user_input: str | None = Field(
        default=None,
        description="Raw user message text from the Telegram update.",
    )
    telegram_user_id: str | None = Field(
        default=None,
        description="Telegram user identifier for the requesting user.",
    )
    next_action: str | None = Field(
        default=None,
        description="Routing hint or node name for the next workflow step.",
    )
    receipt_json: dict[str, Any] | None = Field(
        default=None,
        description="Structured receipt data extracted from user input.",
    )
    file_id: str | None = Field(
        default=None,
        description="Telegram file_id associated with an uploaded receipt or document.",
    )
    expense_id: str | None = Field(
        default=None,
        description="Identifier for the created or matched expense record.",
    )
    status_rows: list[dict[str, Any]] | None = Field(
        default=None,
        description="Status rows (likely from a DB/query) used to build a response.",
    )
    response_text: str | None = Field(
        default=None,
        description="Final response text to send back to the user.",
    )
