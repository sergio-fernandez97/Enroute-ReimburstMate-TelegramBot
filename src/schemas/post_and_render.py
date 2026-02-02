from pydantic import BaseModel, Field

class RenderAndPostResponse(BaseModel):
    """Structured response for render and post"""

    response_text: str = Field(
        ..., description="Final response text for the user determined by the contents in the current state."
    )
