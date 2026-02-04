import logging
import os
from typing import Any

import psycopg

from src.schemas.state import WorkflowState


class UpsertExpenseNode:
    """Create or update an expense record."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("UpsertExpenseNode input state=%s", state)
        return self._run(state)

    def _run(self, state: WorkflowState) -> WorkflowState:
        """Validate receipt data, upsert DB rows, and update workflow state."""
        receipt_json = state.receipt_json
        if not receipt_json:
            logging.warning("UpsertExpenseNode missing receipt_json; skipping upsert.")
            return state

        if not receipt_json.get("is_receipt", False):
            logging.warning("UpsertExpenseNode receipt_json is not a receipt; skipping.")
            return state

        if not state.telegram_user_id:
            logging.warning("UpsertExpenseNode missing telegram_user_id; skipping.")
            return state

        total = self._coerce_amount(receipt_json.get("total"))
        currency = self._normalize_currency(receipt_json.get("currency"))
        expense_date = receipt_json.get("receipt_date")
        if total is None or not currency or not expense_date:
            logging.warning(
                "UpsertExpenseNode missing required fields total=%s currency=%s expense_date=%s",
                total,
                currency,
                expense_date,
            )
            return state

        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            logging.warning("UpsertExpenseNode missing DATABASE_URL; skipping DB write.")
            return state

        try:
            with psycopg.connect(database_url) as conn:
                user_id = self._upsert_user(conn, state)
                expense_id = self._upsert_expense(
                    conn=conn,
                    state=state,
                    receipt_json=receipt_json,
                    user_id=user_id,
                    total=total,
                    currency=currency,
                    expense_date=expense_date,
                )
        except Exception:
            logging.exception("UpsertExpenseNode failed to upsert expense")
            return state

        return state.model_copy(update={"expense_id": str(expense_id)})

    def _upsert_user(self, conn: psycopg.Connection, state: WorkflowState) -> str:
        """Insert or update the user and return the user id."""
        telegram_user_id = self._coerce_telegram_user_id(state.telegram_user_id)
        if telegram_user_id is None:
            raise ValueError("telegram_user_id must be an integer")

        query = """
            INSERT INTO users (telegram_user_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (telegram_user_id)
            DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name
            RETURNING id;
        """.strip()

        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    telegram_user_id,
                    state.username,
                    state.first_name,
                    state.last_name,
                ),
            )
            result = cur.fetchone()
        if not result:
            raise ValueError("Failed to upsert user record")
        return str(result[0])

    def _upsert_expense(
        self,
        conn: psycopg.Connection,
        state: WorkflowState,
        receipt_json: dict[str, Any],
        user_id: str,
        total: float,
        currency: str,
        expense_date: str,
    ) -> str:
        """Insert or update the expense record and return the expense id."""
        description = self._build_description(receipt_json)
        concept = self._normalize_concept(receipt_json)
        file_id = state.file_id

        if state.expense_id:
            expense_id = self._update_expense(
                conn,
                state.expense_id,
                user_id,
                total,
                currency,
                description,
                concept,
                expense_date,
                file_id,
            )
            if expense_id:
                return expense_id

        return self._insert_expense(
            conn,
            user_id,
            total,
            currency,
            description,
            concept,
            expense_date,
            file_id,
        )

    def _update_expense(
        self,
        conn: psycopg.Connection,
        expense_id: str,
        user_id: str,
        total: float,
        currency: str,
        description: str | None,
        concept: str,
        expense_date: str,
        file_id: str | None,
    ) -> str | None:
        """Update an expense row and return its id, or None if not found."""
        query = """
            UPDATE expenses
            SET total = %s,
                currency = %s,
                description = %s,
                concept = %s,
                expense_date = %s,
                file_id = %s,
                updated_at = now()
            WHERE id = %s AND user_id = %s
            RETURNING id;
        """.strip()

        with conn.cursor() as cur:
            cur.execute(
                query,
                (
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
        if not row:
            return None
        return str(row[0])

    def _insert_expense(
        self,
        conn: psycopg.Connection,
        user_id: str,
        total: float,
        currency: str,
        description: str | None,
        concept: str,
        expense_date: str,
        file_id: str | None,
    ) -> str:
        """Insert a new expense and return its id."""
        query = """
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
        """.strip()

        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    user_id,
                    "pending",
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
            raise ValueError("Failed to insert expense record")
        return str(row[0])

    def _build_description(self, receipt_json: dict[str, Any]) -> str | None:
        """Create a human-friendly description for the expense."""
        merchant_name = receipt_json.get("merchant_name")
        if merchant_name:
            return merchant_name
        return receipt_json.get("payment_method")

    def _normalize_concept(self, receipt_json: dict[str, Any]) -> str:
        """Normalize receipt category/concept to a DB enum value."""
        raw_concept = receipt_json.get("concept") or receipt_json.get("category")
        if isinstance(raw_concept, str):
            normalized = raw_concept.strip().lower()
        else:
            normalized = ""

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
        return normalized if normalized in allowed else "otros"

    def _normalize_currency(self, currency: Any) -> str | None:
        """Normalize currency to ISO 4217 uppercase."""
        if not currency:
            return None
        if isinstance(currency, str):
            normalized = currency.strip().upper()
            return normalized if len(normalized) == 3 else None
        return None

    def _coerce_amount(self, value: Any) -> float | None:
        """Coerce an amount to float, returning None if invalid."""
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _coerce_telegram_user_id(self, value: str | None) -> int | None:
        """Coerce telegram_user_id to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
