import os
import unittest
import uuid
from datetime import date

import psycopg

from src.db import init_db
from src.nodes.upsert_expense import UpsertExpense
from src.schemas.state import WorkflowState


@unittest.skipUnless(
    os.getenv("DATABASE_URL"), "DATABASE_URL not set; skipping db-backed tests."
)
class TestUpsertExpense(unittest.TestCase):
    def setUp(self) -> None:
        init_db(os.getenv("DATABASE_URL", ""))
        self.database_url = os.getenv("DATABASE_URL", "")

    def test_upsert_creates_expense_and_updates_state(self):
        telegram_user_id = str(uuid.uuid4().int % 10**12)
        receipt_date = date.today().isoformat()
        state = WorkflowState(
            telegram_user_id=telegram_user_id,
            username="tester",
            first_name="Test",
            last_name="User",
            file_id="file-xyz",
            receipt_json={
                "is_receipt": True,
                "total": 19.99,
                "currency": "usd",
                "receipt_date": receipt_date,
                "merchant_name": "Cafe Demo",
            },
        )

        node = UpsertExpense()
        result = node(state)

        self.assertIsNotNone(result.expense_id)

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT total, currency FROM expenses WHERE id = %s",
                    (result.expense_id,),
                )
                row = cur.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(str(row[1]), "USD")

                cur.execute("DELETE FROM expenses WHERE id = %s", (result.expense_id,))
                cur.execute(
                    "DELETE FROM users WHERE telegram_user_id = %s",
                    (int(telegram_user_id),),
                )


if __name__ == "__main__":
    unittest.main()
