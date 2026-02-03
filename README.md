## Enroute ReimburseMate Bot Workshop

Build a Telegram bot that routes user messages (text + receipts) through a LangGraph workflow. The goal is to show how Codex can accelerate safe, incremental development.

## Who this workshop is for
- Software engineers and technical product/platform teams
- Anyone comfortable reading code and basic Git

This is not an intro to Python or LLM theory.

## Tech stack
- Python 3.13+
- LangChain + LangGraph
- OpenAI API (vision + tools)
- Telegram API
- PostgreSQL (optional, SQLite in demos)
- MinIO (optional, for file storage)
- Docker
- Codex (coding assistant)

## Workshop flow (high level)
1. Prerequisites and repo tour
2. Codex setup
3. Telegram bot setup
4. Review existing structure: schemas, tools, prompts, AGENTS.md
5. Run the starter bot
6. Walk the AI workflow diagram and build nodes
7. Implement the planner (agent plan)
8. Orchestrate the creation of nodes: `extract_receipt`, `query_status`, `render_and_post`, `upsert_expense`
9. Compile and test the full graph.

## Prerequisites
- Python 3.13+
- A Telegram bot token
- OpenAI API key
- Docker 

Optional:
- PostgreSQL connection string
- MinIO endpoint + credentials

## Credentials (env vars)
Create a `.env` file at the repo root:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
OPENAI_API_KEY=your_openai_api_key

# Optional (used if set)
DATABASE_URL=postgresql://user:password@localhost:5432/reimburstmate
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=reimburstmate
```

## Setup

### 1) Create your Telegram bot
1. Open Telegram and message `@BotFather`.
2. Send `/start`, then `/newbot`.
3. Choose a display name (e.g., "Enroute ReimburstMate Bot").
4. Choose a username (e.g., `enroute_reimburse_bot`).
5. Save the token and add it to `TELEGRAM_BOT_TOKEN` in `.env`.

### 2) Install dependencies
Use your preferred Python toolchain:
```bash
# Option A (uv)
uv sync

# Option B (pip)
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3) Run the bot
```bash
uv run python app.py
```

You should see:
- "Bot is running! Press Ctrl+C to stop."

### 4) (Optional) Connect Codex to Context7
Context7 is a free MCP server for developer docs.
```bash
codex mcp add context7 -- npx -y @upstash/context7-mcp
```

## Repo map (quick)
- `app.py`: Telegram bot entry point and handlers
- `src/graph/`: LangGraph wiring
- `src/nodes/`: Node implementations
- `src/schemas/`: Pydantic workflow state
- `src/tools/`: Tooling (image extraction, MinIO, etc.)
- `tests/`: Unit tests for nodes

## Agent architecture (overview)

### Agent plan (planner)
- Role: Brain and router
- Inputs: user message + current workflow state
- Outputs: `next_action`, `tool_args`, optional `message_to_user`

### extract_receipt
- Role: Vision/perception
- Inputs: receipt images/PDFs
- Outputs: `receipt_json`

### upsert_expense
- Role: Write to system of record
- Inputs: validated receipt data
- Outputs: `expense_id`

### query_status
- Role: Memory retrieval (read DB)
- Inputs: filters from user message
- Outputs: `status_rows`

### render_and_post
- Role: UX layer for user-facing responses
- Inputs: workflow state
- Outputs: Telegram message

### END
- Role: Explicit termination
- Ends when the task completes or user input is required

## Tools

### Image Extractor
Extracts receipt contents as structured data.

Test:
```bash
uv run python src/tools/image_extractor.py --image-path images/receipts/invalid_receipt.jpg
```

Expected (example):
```json
{
  "is_receipt": true,
  "merchant_name": "Uber",
  "merchant_address": null,
  "receipt_date": "2025-11-16",
  "receipt_time": "14:59",
  "currency": "MXN",
  "subtotal": null,
  "tax": null,
  "tip": null,
  "total": 197.97,
  "payment_method": "Amex",
  "items": [
    {
      "description": "Trip fare",
      "quantity": 1.0,
      "unit_price": 235.45,
      "line_total": 235.45
    }
  ]
}
```

## Troubleshooting
- If the bot exits immediately, confirm `TELEGRAM_BOT_TOKEN` is set.
- If DB init fails, check `DATABASE_URL` or leave it unset for a demo run.
- If MinIO upload fails, set `MINIO_*` vars or skip file uploads.
