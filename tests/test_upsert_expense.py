import unittest
from unittest.mock import MagicMock, patch

from src.nodes.upsert_expense import UpsertExpense
from src.schemas.state import WorkflowState


def _build_mock_connection(fetchone_results):
    cur = MagicMock()
    cur.fetchone.side_effect = fetchone_results

    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = cur

    conn = MagicMock()
    conn.cursor.return_value = cursor_cm

    conn_cm = MagicMock()
    conn_cm.__enter__.return_value = conn
    return conn_cm, cur


class UpsertExpenseTests(unittest.TestCase):
    def test_upsert_skips_without_receipt(self) -> None:
        state = WorkflowState(telegram_user_id="123")

        with patch("src.nodes.upsert_expense.psycopg.connect") as connect:
            updated_state = UpsertExpense()(state)

        connect.assert_not_called()
        self.assertIsNone(updated_state.expense_id)

    def test_upsert_inserts_expense(self) -> None:
        receipt = {
            "is_receipt": True,
            "merchant_name": "Uber",
            "receipt_date": "2025-11-16",
            "currency": "mxn",
            "total": 197.97,
            "payment_method": "Amex",
            "category": "transporte",
        }
        state = WorkflowState(
            telegram_user_id="123",
            username="tester",
            first_name="Test",
            last_name="User",
            receipt_json=receipt,
        )

        conn_cm, cur = _build_mock_connection(
            [("user-uuid",), ("expense-uuid",)]
        )
        with patch("src.nodes.upsert_expense.psycopg.connect", return_value=conn_cm):
            with patch.dict("os.environ", {"DATABASE_URL": "db"}):
                updated_state = UpsertExpense()(state)

        self.assertEqual(updated_state.expense_id, "expense-uuid")
        self.assertGreaterEqual(cur.execute.call_count, 2)

    def test_upsert_updates_existing_expense(self) -> None:
        receipt = {
            "is_receipt": True,
            "merchant_name": "Uber",
            "receipt_date": "2025-11-16",
            "currency": "mxn",
            "total": "197.97",
        }
        state = WorkflowState(
            telegram_user_id="123",
            receipt_json=receipt,
            expense_id="expense-old",
        )

        conn_cm, _cur = _build_mock_connection(
            [("user-uuid",), ("expense-old",)]
        )
        with patch("src.nodes.upsert_expense.psycopg.connect", return_value=conn_cm):
            with patch.dict("os.environ", {"DATABASE_URL": "db"}):
                updated_state = UpsertExpense()(state)

        self.assertEqual(updated_state.expense_id, "expense-old")


if __name__ == "__main__":
    unittest.main()
