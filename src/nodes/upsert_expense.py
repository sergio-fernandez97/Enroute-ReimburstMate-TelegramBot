import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

import psycopg

from src.schemas.state import WorkflowState


@dataclass(frozen=True)
class ExpensePayload:
    """Normalized data required to insert or update an expense."""

    total: float
    currency: str
    description: str | None
    concept: str | None
    expense_date: date
    file_id: str | None


class UpsertExpense:
    """Create or update an expense record based on receipt data."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.
            config: Node configuration.

        Returns:
            Updated workflow state.
        """
        logging.info("UpsertExpense input state=%s", state)
        return self._upsert(state)

    def _upsert(self, state: WorkflowState) -> WorkflowState:
        """Persist the expense data and update state with expense_id."""
        receipt_json = state.receipt_json or {}
        if not receipt_json:
            logging.info("UpsertExpense skipped: missing receipt_json.")
            return state

        payload = self._build_payload(state, receipt_json)
        if payload is None:
            logging.warning("UpsertExpense skipped: insufficient receipt data.")
            return state

        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            logging.warning("DATABASE_URL not set; skipping expense upsert.")
            return state

        expense_id = self._persist(database_url, state, payload)
        if not expense_id:
            logging.warning("UpsertExpense did not return an expense_id.")
            return state

        return state.model_copy(update={"expense_id": expense_id})

    def _build_payload(
        self, state: WorkflowState, receipt_json: dict[str, Any]
    ) -> Optional[ExpensePayload]:
        """Normalize state and receipt JSON into a DB-friendly payload."""
        total = self._coerce_float(receipt_json.get("total"))
        if total is None:
            total = self._coerce_float(receipt_json.get("subtotal"))
        if total is None:
            return None

        currency = self._normalize_currency(receipt_json.get("currency"))
        expense_date = self._normalize_date(receipt_json.get("receipt_date"))
        description = receipt_json.get("merchant_name") or state.user_input
        concept = self._normalize_concept(receipt_json.get("concept"))

        return ExpensePayload(
            total=total,
            currency=currency,
            description=description,
            concept=concept,
            expense_date=expense_date,
            file_id=state.file_id,
        )

    def _persist(
        self, database_url: str, state: WorkflowState, payload: ExpensePayload
    ) -> Optional[str]:
        """Insert or update user/expense records and return expense_id."""
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                user_id = self._upsert_user(cur, state)
                if not user_id:
                    return None
                if state.expense_id:
                    expense_id = self._update_expense(cur, state.expense_id, payload, user_id)
                else:
                    expense_id = self._insert_expense(cur, payload, user_id)
            conn.commit()
        return expense_id

    def _upsert_user(self, cur: psycopg.Cursor, state: WorkflowState) -> Optional[str]:
        """Insert or update the user row and return user id."""
        if not state.telegram_user_id:
            logging.warning("UpsertExpense skipped: missing telegram_user_id.")
            return None

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
                int(state.telegram_user_id),
                state.username,
                state.first_name,
                state.last_name,
            ),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def _insert_expense(
        self, cur: psycopg.Cursor, payload: ExpensePayload, user_id: str
    ) -> Optional[str]:
        """Insert a new expense row and return expense id."""
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
                payload.total,
                payload.currency,
                payload.description,
                payload.concept,
                payload.expense_date,
                payload.file_id,
            ),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def _update_expense(
        self,
        cur: psycopg.Cursor,
        expense_id: str,
        payload: ExpensePayload,
        user_id: str,
    ) -> Optional[str]:
        """Update an existing expense and return the expense id."""
        cur.execute(
            """
            UPDATE expenses
            SET
                user_id = %s,
                total = %s,
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
                user_id,
                payload.total,
                payload.currency,
                payload.description,
                payload.concept,
                payload.expense_date,
                payload.file_id,
                expense_id,
            ),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def _coerce_float(self, value: Any) -> Optional[float]:
        """Coerce numeric-like values into float."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return None

    def _normalize_currency(self, currency: Any) -> str:
        """Normalize currency code to a 3-letter uppercase string."""
        if not currency:
            return "USD"
        code = str(currency).strip().upper()
        return code[:3] if len(code) >= 3 else code.ljust(3, "X")

    def _normalize_date(self, value: Any) -> date:
        """Normalize date string into a date instance."""
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        return date.today()

    def _normalize_concept(self, concept: Any) -> Optional[str]:
        """Map receipt concept to a supported enum value."""
        if not concept:
            return "otros"
        normalized = str(concept).strip().lower()
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
        if normalized in allowed:
            return normalized
        return "otros"
