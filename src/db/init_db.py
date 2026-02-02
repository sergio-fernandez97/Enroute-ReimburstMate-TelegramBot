import logging
import os
from typing import Iterable

import psycopg


logger = logging.getLogger(__name__)


def _statements() -> Iterable[str]:
    return [
        "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
        """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'expense_concept') THEN
        CREATE TYPE expense_concept AS ENUM (
            'alimentos',
            'avion',
            'estacionamiento',
            'gasto de oficina',
            'hotel',
            'otros',
            'profesional development',
            'transporte',
            'eventos'
        );
    END IF;
END $$;
""".strip(),
        """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
""".strip(),
        """
CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    status TEXT NOT NULL CHECK (status IN ('approved', 'not_approved', 'pending')),
    total NUMERIC(12, 2) NOT NULL,
    currency CHAR(3) NOT NULL,
    description TEXT,
    concept expense_concept,
    expense_date DATE NOT NULL,
    file_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
""".strip(),
        "CREATE INDEX IF NOT EXISTS expenses_user_id_idx ON expenses(user_id);",
        "CREATE INDEX IF NOT EXISTS expenses_status_idx ON expenses(status);",
        "CREATE INDEX IF NOT EXISTS expenses_expense_date_idx ON expenses(expense_date);",
    ]


def init_db(database_url: str) -> None:
    """Ensure required tables and types exist."""
    if not database_url:
        logger.warning("DATABASE_URL not set; skipping DB initialization")
        return

    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                for statement in _statements():
                    cur.execute(statement)
        logger.info("Database schema ensured")
    except Exception:
        logger.exception("Failed to initialize database")
        raise


def init_db_from_env() -> None:
    """Initialize database using DATABASE_URL from env."""
    init_db(os.getenv("DATABASE_URL", ""))
