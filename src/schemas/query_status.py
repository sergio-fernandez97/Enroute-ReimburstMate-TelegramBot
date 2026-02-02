from pydantic import BaseModel, Field

class QueryStatusResponse(BaseModel):
    """Structured response for query status."""
    queries: list[str] | None = Field(
        default=None, description="queries needed in order to retrieve the information need by the user."
    )