import unittest

from src.nodes.upsert_expense import UpsertExpense
from src.schemas.state import WorkflowState


class TestUpsertExpense(unittest.TestCase):
    def test_skips_without_receipt_json(self) -> None:
        node = UpsertExpense(database_url="")
        state = WorkflowState(telegram_user_id="12345")

        result = node(state)

        self.assertIsNone(result.expense_id)

    def test_sets_demo_expense_id_without_database(self) -> None:
        node = UpsertExpense(database_url="")
        state = WorkflowState(
            telegram_user_id="12345",
            receipt_json={
                "is_receipt": True,
                "merchant_name": "Cafe",
                "receipt_date": "2025-11-16",
                "currency": "usd",
                "total": 15.5,
            },
        )

        result = node(state)

        self.assertIsNotNone(result.expense_id)
        self.assertTrue(result.expense_id.startswith("demo-"))


if __name__ == "__main__":
    unittest.main()
