import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

import psycopg

from src.schemas.state import WorkflowState


class UpsertExpense:
    """Creates or updates an expense record in the system of record."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("UpsertExpense input state=%s", state)
        return self._upsert(state)

    def _upsert(self, state: WorkflowState) -> WorkflowState:
        """Upsert receipt data into the database and return updated state."""
        if not state.receipt_json:
            logging.info("UpsertExpense skipping: missing receipt_json")
            return state
        if state.receipt_json.get("is_receipt") is False:
            logging.info("UpsertExpense skipping: receipt marked as invalid")
            return state
        if not state.telegram_user_id:
            logging.warning("UpsertExpense missing telegram_user_id; skipping DB write")
            return state

        total = self._coerce_decimal(state.receipt_json.get("total"))
        currency = self._normalize_currency(state.receipt_json.get("currency"))
        expense_date = state.receipt_json.get("receipt_date")

        if total is None or not currency or not expense_date:
            logging.warning(
                "UpsertExpense missing required fields total=%s currency=%s expense_date=%s",
                total,
                currency,
                expense_date,
            )
            return state

        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            logging.warning("DATABASE_URL not set; skipping expense upsert.")
            return state

        description = self._build_description(state.receipt_json)
        concept = self._normalize_concept(state.receipt_json.get("category"))
        status = state.receipt_json.get("status") or "pending"

        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                user_id = self._upsert_user(cur, state)
                expense_id = self._upsert_expense(
                    cur,
                    user_id=user_id,
                    expense_id=state.expense_id,
                    status=status,
                    total=total,
                    currency=currency,
                    description=description,
                    concept=concept,
                    expense_date=expense_date,
                    file_id=state.file_id,
                )

        return state.model_copy(update={"expense_id": expense_id})

    def _upsert_user(self, cur: psycopg.Cursor[Any], state: WorkflowState) -> str:
        """Upsert the user row and return the user id."""
        cur.execute(
            """
            INSERT INTO users (telegram_user_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (telegram_user_id) DO UPDATE
            SET username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name
            RETURNING id
            """,
            (
                int(state.telegram_user_id),
                state.username,
                state.first_name,
                state.last_name,
            ),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Failed to upsert user record")
        return str(row[0])

    def _upsert_expense(
        self,
        cur: psycopg.Cursor[Any],
        *,
        user_id: str,
        expense_id: Optional[str],
        status: str,
        total: Decimal,
        currency: str,
        description: Optional[str],
        concept: Optional[str],
        expense_date: str,
        file_id: Optional[str],
    ) -> str:
        """Insert or update the expense row and return the expense id."""
        if expense_id:
            cur.execute(
                """
                UPDATE expenses
                SET status = %s,
                    total = %s,
                    currency = %s,
                    description = %s,
                    concept = %s,
                    expense_date = %s,
                    file_id = %s,
                    updated_at = now()
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (
                    status,
                    total,
                    currency,
                    description,
                    concept,
                    expense_date,
                    file_id,
                    expense_id,
                    user_id,
                ),
            )
            row = cur.fetchone()
            if row:
                return str(row[0])

        cur.execute(
            """
            INSERT INTO expenses (
                user_id,
                status,
                total,
                currency,
                description,
                concept,
                expense_date,
                file_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user_id,
                status,
                total,
                currency,
                description,
                concept,
                expense_date,
                file_id,
            ),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Failed to insert expense record")
        return str(row[0])

    def _coerce_decimal(self, value: Any) -> Optional[Decimal]:
        """Convert receipt numeric fields to Decimal safely."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _normalize_currency(self, value: Any) -> Optional[str]:
        """Normalize currency codes to uppercase ISO-4217 style."""
        if not value:
            return None
        return str(value).strip().upper()

    def _build_description(self, receipt: Dict[str, Any]) -> Optional[str]:
        """Build a short description for the expense."""
        merchant = receipt.get("merchant_name")
        payment = receipt.get("payment_method")
        if merchant and payment:
            return f"{merchant} ({payment})"
        return merchant or payment

    def _normalize_concept(self, value: Any) -> Optional[str]:
        """Return a valid expense_concept enum value or None."""
        if not value:
            return None
        normalized = str(value).strip().lower()
        allowed = {
            "alimentos",
            "avion",
            "estacionamiento",
            "gasto de oficina",
            "hotel",
            "otros",
            "profesional development",
            "transporte",
            "eventos",
        }
        return normalized if normalized in allowed else None
