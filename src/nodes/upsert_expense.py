import logging
import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import psycopg

from src.schemas.state import WorkflowState


class UpsertExpense:
    """Create or update an expense record based on extracted data."""

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
        """Write expense data and update the state."""
        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            logging.warning("DATABASE_URL not set; skipping expense upsert")
            return state

        receipt = self._normalize_receipt(state)
        if receipt is None:
            logging.warning("Receipt data incomplete; skipping expense upsert")
            return state

        user_id = self._upsert_user(state, database_url)
        if not user_id:
            logging.warning("Unable to resolve user id; skipping expense upsert")
            return state

        expense_id = self._upsert_expense(state, receipt, user_id, database_url)
        if expense_id:
            state.expense_id = str(expense_id)
        return state

    def _upsert_user(self, state: WorkflowState, database_url: str) -> str | None:
        """Create or update the user record.

        Args:
            state: Current workflow state.
            database_url: Database connection URL.

        Returns:
            User id if successful.
        """
        if not state.telegram_user_id:
            return None

        telegram_user_id = self._safe_int(state.telegram_user_id)
        if telegram_user_id is None:
            return None

        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (telegram_user_id, username, first_name, last_name)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (telegram_user_id)
                    DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name
                    RETURNING id;
                    """,
                    (
                        telegram_user_id,
                        state.username,
                        state.first_name,
                        state.last_name,
                    ),
                )
                row = cur.fetchone()
                return str(row[0]) if row else None

    def _upsert_expense(
        self,
        state: WorkflowState,
        receipt: "NormalizedReceipt",
        user_id: str,
        database_url: str,
    ) -> str | None:
        """Create or update an expense row.

        Args:
            state: Current workflow state.
            receipt: Normalized receipt data.
            user_id: Owner user id.
            database_url: Database connection URL.

        Returns:
            Expense id if successful.
        """
        description = receipt.description
        concept = receipt.concept

        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                if state.expense_id:
                    cur.execute(
                        """
                        UPDATE expenses
                        SET total = %s,
                            currency = %s,
                            description = %s,
                            concept = %s,
                            expense_date = %s,
                            file_id = %s,
                            updated_at = now()
                        WHERE id = %s
                        RETURNING id;
                        """,
                        (
                            receipt.total,
                            receipt.currency,
                            description,
                            concept,
                            receipt.expense_date,
                            state.file_id,
                            state.expense_id,
                        ),
                    )
                else:
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
                        RETURNING id;
                        """,
                        (
                            user_id,
                            "pending",
                            receipt.total,
                            receipt.currency,
                            description,
                            concept,
                            receipt.expense_date,
                            state.file_id,
                        ),
                    )
                row = cur.fetchone()
                return str(row[0]) if row else None

    def _normalize_receipt(
        self, state: WorkflowState
    ) -> "NormalizedReceipt" | None:
        """Normalize receipt info needed for persistence."""
        if not isinstance(state.receipt_json, dict):
            return None
        if not state.receipt_json.get("is_receipt", False):
            return None

        total = self._safe_decimal(state.receipt_json.get("total"))
        currency = state.receipt_json.get("currency")
        receipt_date = state.receipt_json.get("receipt_date")

        if total is None or not currency:
            return None

        normalized_date = self._normalize_date(receipt_date)
        description = state.receipt_json.get("merchant_name") or state.receipt_json.get(
            "description"
        )

        return NormalizedReceipt(
            total=total,
            currency=str(currency).upper(),
            expense_date=normalized_date,
            description=description,
            concept=str(state.receipt_json.get("concept") or "otros"),
        )

    def _safe_int(self, value: Any) -> int | None:
        """Convert numeric-like values into int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _safe_decimal(self, value: Any) -> Decimal | None:
        """Convert numeric-like values into Decimal."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _normalize_date(self, value: Any) -> date:
        """Normalize date string into a date object."""
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        return date.today()


@dataclass(frozen=True)
class NormalizedReceipt:
    """Normalized receipt data required for persistence."""

    total: Decimal
    currency: str
    expense_date: date
    description: str | None
    concept: str
