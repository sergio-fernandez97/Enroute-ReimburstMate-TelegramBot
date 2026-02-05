## Enroute ReimburstMate Bot Workshop

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

## Before the workshop

### Prerequisites
- Python installed
- Visual Studio Code (optional)
- Codex installed
- `OPENAI_API_KEY` set
- Docker installed

### What’s already done
- Service skeleton
- Schemas:
  - State
  - Receipt
  - AgentPlanResponse
- Docker compose configuration
- Tools:
  - Image Extractor
- Prompts:
  - Image Extractor
  - Agent Plan Response
- [AGENTS.md](./AGENTS.md): guidelines for the coding assistant

## Workshop steps (detailed)
1. Clone this repo:
   ```bash
   git clone -b workshop-feb-3 git@github.com:sergio-fernandez97/Enroute-ReimburseMate-TelegramBot.git
   ```
2. Configure your own bot:
   - Open Telegram and message `@BotFather`.
   - Send `/start`, then `/newbot`.
   - Choose a display name (e.g., "Enroute ReimburseMate Bot").
   - Choose a username (e.g., `enroute_reimburse_bot`).
   - Save the token and add it to `TELEGRAM_BOT_TOKEN` in `.env`.

   ![bot_father](./images/bot_father.png)
3. Launch your app and test it with Telegram:
   ```bash
   docker compose up --build
   ```
4. Review the [AGENTS.md](./AGENTS.md).
5. Install the MCP server ![Context7](https://context7.com) for codex:
```bash 
codex mcp add context7 -- npx -y @upstash/context7-mcp
```
6. Show the workflow in a diagram. Take a screenshot and give it to Codex to create the agent with LangGraph (empty nodes).
   ```
   Use Context7 to fetch the official LangGraph documentation. Look at the diagram in the image, which represents the workflow we want to build. Help me populate the nodes and include the graph in src/graph/graph.py. Leave the logic of each node empty, we will work on that later.
   ```
7. Show the state: Pydantic model (information flowing through the process) at `src/schemas/state.py`.
8. Validate the created code (optional): plot the graph in a notebook.
   ```
   Use Context7 to fetch the official LangGraph documentation. And create a notebook named graph.ipynb. In one cell compile the graph (from src.graph.graph import graph) as "app". Then plot the complete graph.
   ```
9. Create the brain node (agent plan).
   ```
   Use Context7 to fetch the official LangGraph and LangChain documentation. And fill the node @src/nodes/agent_plan.py. Load the prompt in @src/prompts/agent_plan.md and create chain with the structured output in @src/schemas/agent_plan.py, then format the state in order to complete the prompt. Afterwards invoke the llm with structured output, extract the field next action and update the state.
   ```
10. Test image extractor tool (script:![image_extractor.py](./src/tools/image_extractor.py)):
```bash
uv run python src/tools/image_extractor.py --
```
11. With multi-agent functionality create the nodes: `extract_receipt`, `query_status`, `render_and_post`, `upsert_expense`.
    11.1 `extract_receipt`:
     ```
     Use Context7 to fetch the official LangGraph documentation. Fill the node @src/nodes/extract_receipt.py. Read the node description at @README.md. Then load the bytes of the image given the file_id in the state, call the tool for extracting the information from the file: @src/tools/images_extractor.py and then fill receipt_json with the information.
     ```
    11.2 `query_status`:
     ```
     Fill the node @src/nodes/query_status.py. Read the node description at @README.md. Load the prompt from @src/prompts/query_status.md and create a chain with the structured output given by @src/schemas/query_status.py, then include the user message in the request to the llm. Invoke the llm, extract the field queries if it is not null use the queries for retrieving the need information and fill the state field named status_rows.
     ```
    11.3 `render_and_post`:
     ```
     Fill the node @src/nodes/post_and_render.py. Read the node description at @README.md. Load the prompt from @src/prompts/post_and_render.md and create a chain with structured output given by @src/schemas/post_and_render.py, then include the current state in the request of the llm. Invoke the llm, extract the field response_text and update the state.
     ```
    11.4 `upsert_expense`:
     ```
     Fill the node @src/nodes/upsert_expense.py. Read the node description at @README.md. Upsert the needed information from state in sql tables and update state with expense_id.
     ```
12. Compile the graph in the app (use https://chatgpt.com/codex if helpful):
    ```
    Import the graph from @src/graph/graph.py into @app.py and compile it. In @app.py modify the coroutines handle_text and handle_photo in order append the file and telegram user information to the state and then to invoke the graph. Afterwards extract the response from the workflow and return it to telegram.
    ```
13. Test the bot and fix troubleshootings.

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
3. Choose a display name (e.g., "Enroute ReimburseMate Bot").
4. Choose a username (e.g., `enroute_reimburse_bot`).
5. Save the token and add it to `TELEGRAM_BOT_TOKEN` in `.env`.

### 2) Install dependencies
Use your preferred Python toolchain:

```bash
# Option A (uv)
uv sync
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
