import logging
import os
import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import psycopg

from src.schemas.state import WorkflowState


class UpsertExpense:
    """Creates or updates an expense record."""

    def __init__(self, database_url: str | None = None) -> None:
        self._database_url = database_url or os.getenv("DATABASE_URL", "")

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
        """Persist receipt data and update state with expense_id."""
        receipt = state.receipt_json or {}
        if not receipt:
            logging.warning("UpsertExpense skipped: receipt_json missing")
            return state

        if receipt.get("is_receipt") is False:
            logging.warning("UpsertExpense skipped: receipt_json marked invalid receipt")
            return state

        telegram_user_id = self._normalize_telegram_user_id(state.telegram_user_id)
        if telegram_user_id is None:
            logging.warning("UpsertExpense skipped: telegram_user_id missing or invalid")
            return self._set_demo_expense_id(state)

        expense_payload = self._build_expense_payload(state, receipt)

        if not self._database_url:
            logging.warning("DATABASE_URL not set; using demo expense_id")
            return self._set_demo_expense_id(state)

        try:
            expense_id = self._upsert_db(
                telegram_user_id=telegram_user_id,
                username=state.username,
                first_name=state.first_name,
                last_name=state.last_name,
                expense_id=state.expense_id,
                payload=expense_payload,
            )
            state.expense_id = expense_id
            return state
        except Exception:
            logging.exception("Failed to upsert expense; falling back to demo expense_id")
            return self._set_demo_expense_id(state)

    def _normalize_telegram_user_id(self, telegram_user_id: str | None) -> int | None:
        if telegram_user_id is None:
            return None
        try:
            return int(telegram_user_id)
        except (TypeError, ValueError):
            return None

    def _build_expense_payload(
        self, state: WorkflowState, receipt: dict[str, Any]
    ) -> dict[str, Any]:
        total = receipt.get("total")
        if total is None:
            subtotal = receipt.get("subtotal") or 0
            tax = receipt.get("tax") or 0
            tip = receipt.get("tip") or 0
            total = subtotal + tax + tip

        currency = (receipt.get("currency") or "USD").upper()
        expense_date = self._parse_date(receipt.get("receipt_date"))
        description = receipt.get("merchant_name") or state.user_input or "Receipt expense"
        concept = receipt.get("concept")

        return {
            "status": "pending",
            "total": Decimal(str(total)),
            "currency": currency,
            "description": description,
            "concept": concept,
            "expense_date": expense_date,
            "file_id": state.file_id,
        }

    def _parse_date(self, raw_date: str | None) -> date:
        if not raw_date:
            return date.today()
        try:
            return date.fromisoformat(raw_date)
        except ValueError:
            return date.today()

    def _upsert_db(
        self,
        telegram_user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        expense_id: str | None,
        payload: dict[str, Any],
    ) -> str:
        with psycopg.connect(self._database_url) as conn:
            with conn.cursor() as cur:
                user_id = self._upsert_user(
                    cur,
                    telegram_user_id=telegram_user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
                updated_id = None
                if expense_id:
                    updated_id = self._update_expense(
                        cur,
                        expense_id=expense_id,
                        user_id=user_id,
                        payload=payload,
                    )
                if updated_id:
                    return updated_id
                return self._insert_expense(cur, user_id=user_id, payload=payload)

    def _upsert_user(
        self,
        cur: psycopg.Cursor,
        telegram_user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> str:
        cur.execute(
            """
            INSERT INTO users (telegram_user_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (telegram_user_id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name
            RETURNING id;
            """,
            (telegram_user_id, username, first_name, last_name),
        )
        row = cur.fetchone()
        return str(row[0])

    def _update_expense(
        self,
        cur: psycopg.Cursor,
        expense_id: str,
        user_id: str,
        payload: dict[str, Any],
    ) -> str | None:
        cur.execute(
            """
            UPDATE expenses
            SET user_id = %s,
                status = %s,
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
                payload["status"],
                payload["total"],
                payload["currency"],
                payload["description"],
                payload["concept"],
                payload["expense_date"],
                payload["file_id"],
                expense_id,
            ),
        )
        row = cur.fetchone()
        if row:
            return str(row[0])
        return None

    def _insert_expense(
        self, cur: psycopg.Cursor, user_id: str, payload: dict[str, Any]
    ) -> str:
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
                payload["status"],
                payload["total"],
                payload["currency"],
                payload["description"],
                payload["concept"],
                payload["expense_date"],
                payload["file_id"],
            ),
        )
        row = cur.fetchone()
        return str(row[0])

    def _set_demo_expense_id(self, state: WorkflowState) -> WorkflowState:
        state.expense_id = f"demo-{uuid.uuid4()}"
        return state
