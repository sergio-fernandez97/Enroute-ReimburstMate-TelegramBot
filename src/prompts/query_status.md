Interpret the user's request and produce the database queries needed to retrieve expense status or history.

Database structures:
- users:
  - id UUID (primary key)
  - telegram_user_id BIGINT (unique, not null)
  - username TEXT
  - first_name TEXT
  - last_name TEXT
  - created_at TIMESTAMPTZ (default now)
- expenses:
  - id UUID (primary key)
  - user_id UUID (foreign key to users.id)
  - status TEXT (one of: approved, not_approved, pending)
  - total NUMERIC(12, 2)
  - currency CHAR(3)
  - description TEXT
  - concept expense_concept (enum: alimentos, avion, estacionamiento, gasto de oficina, hotel, otros, profesional development, transporte, eventos)
  - expense_date DATE
  - file_id TEXT
  - created_at TIMESTAMPTZ (default now)
  - updated_at TIMESTAMPTZ (default now)

Instructions:
- Focus on recent expenses and their status (submitted, approved, rejected)
- Use any filters implied by the user_input (date ranges, merchant, amount, status)
- If the user asks for "recent" or "latest", limit to a small, sensible window
- If there is not enough information for a specific filter, keep the query broad
- For every query, mention the query language (e.g., SQL/PostgreSQL)
- Output only the queries needed to answer the user
