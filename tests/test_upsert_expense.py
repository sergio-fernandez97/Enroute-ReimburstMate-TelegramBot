import os
import unittest
from unittest.mock import patch

from src.nodes.upsert_expense import UpsertExpenseNode
from src.schemas.state import WorkflowState


class _DummyConn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestUpsertExpenseNode(unittest.TestCase):
    def test_skips_without_receipt_json(self) -> None:
        node = UpsertExpenseNode()
        state = WorkflowState(telegram_user_id="123")

        with patch("src.nodes.upsert_expense.psycopg.connect") as connect:
            result = node(state)

        connect.assert_not_called()
        self.assertIs(result, state)

    def test_skips_when_not_a_receipt(self) -> None:
        node = UpsertExpenseNode()
        state = WorkflowState(
            telegram_user_id="123",
            receipt_json={"is_receipt": False},
        )

        with patch("src.nodes.upsert_expense.psycopg.connect") as connect:
            result = node(state)

        connect.assert_not_called()
        self.assertIs(result, state)

    def test_updates_state_with_expense_id(self) -> None:
        node = UpsertExpenseNode()
        receipt_json = {
            "is_receipt": True,
            "total": 18.75,
            "currency": "usd",
            "receipt_date": "2025-11-16",
            "merchant_name": "Cafe",
        }
        state = WorkflowState(
            telegram_user_id="123",
            username="tester",
            first_name="Test",
            last_name="User",
            file_id="file-123",
            receipt_json=receipt_json,
        )

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://example"}):
            with patch(
                "src.nodes.upsert_expense.psycopg.connect", return_value=_DummyConn()
            ) as connect:
                with patch.object(node, "_upsert_user", return_value="user-1") as upsert_user:
                    with patch.object(
                        node, "_upsert_expense", return_value="expense-1"
                    ) as upsert_expense:
                        result = node(state)

        connect.assert_called_once_with("postgresql://example")
        upsert_user.assert_called_once()
        upsert_expense.assert_called_once()
        self.assertEqual(result.expense_id, "expense-1")
        self.assertEqual(result.receipt_json, receipt_json)


if __name__ == "__main__":
    unittest.main()
