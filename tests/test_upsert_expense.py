import os
import unittest
from unittest.mock import MagicMock, patch

from src.nodes.upsert_expense import UpsertExpense
from src.schemas.state import WorkflowState


class TestUpsertExpense(unittest.TestCase):
    def test_upsert_expense_sets_expense_id(self) -> None:
        state = WorkflowState(
            telegram_user_id="12345",
            username="tester",
            first_name="Test",
            last_name="User",
            file_id="file_123",
            receipt_json={
                "total": 42.5,
                "currency": "usd",
                "receipt_date": "2025-11-16",
                "merchant_name": "Test Cafe",
            },
        )

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [("user-id",), ("expense-id",)]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}):
            with patch("src.nodes.upsert_expense.psycopg.connect") as mock_connect:
                mock_connect.return_value.__enter__.return_value = mock_conn

                updated = UpsertExpense()(state)

        self.assertEqual(updated.expense_id, "expense-id")
        mock_connect.assert_called_once()
        self.assertEqual(mock_cursor.execute.call_count, 2)

    def test_upsert_expense_skips_without_receipt_json(self) -> None:
        state = WorkflowState(telegram_user_id="12345")

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}):
            with patch("src.nodes.upsert_expense.psycopg.connect") as mock_connect:
                updated = UpsertExpense()(state)

        self.assertIsNone(updated.expense_id)
        mock_connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
