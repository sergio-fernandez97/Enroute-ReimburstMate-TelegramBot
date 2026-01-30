from pydantic import BaseModel, Field

class ReceiptItem(BaseModel):
    """Individual line item on a receipt."""
    description: str = Field(description="Name or description of the item")
    quantity: float | None = Field(default=None, description="Quantity purchased")
    unit_price: float | None = Field(default=None, description="Price per unit")
    line_total: float | None = Field(default=None, description="Total for this line item")


class Receipt(BaseModel):
    """Structured representation of a receipt."""
    is_receipt: bool = Field(default=False, description="Determine if the provided image is or not a valid receipt.")
    merchant_name: str | None = Field(default=None, description="Name of the merchant/store")
    merchant_address: str | None = Field(default=None, description="Address of the merchant")
    receipt_date: str | None = Field(default=None, description="Date in YYYY-MM-DD format")
    receipt_time: str | None = Field(default=None, description="Time in HH:MM format")
    currency: str | None = Field(default=None, description="ISO 4217 code (MXN, USD, EUR)")
    subtotal: float | None = Field(default=None, description="Subtotal before tax")
    tax: float | None = Field(default=None, description="Tax amount")
    tip: float | None = Field(default=None, description="Tip amount if applicable")
    total: float | None = Field(default=None, description="Total amount paid")
    payment_method: str | None = Field(default=None, description="Cash, credit card, etc.")
    items: list[ReceiptItem] | None = Field(default_factory=list, description="List of purchased items")