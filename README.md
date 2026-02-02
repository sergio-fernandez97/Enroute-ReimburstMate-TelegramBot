
## 1. Setup
### 1.x Telegram 

### 1.x.y Get your own bot 
1. Go to @BotFather and send the commad `/start`, a menu with all commands will be displayed.
2. Now write the command `\newbot`, this will allow you to configure your own bot. 
    - First, give a name to the bot (not a username) for instance **Enroute ReinmburstMate Bot**.
    - Then assign a username  for instance **enroute_reimburse_bot**.
    - If the username is available you will receive a confirmation. Get your token and store it into an environment variable named `TELEGRAM_BOT_TOKEN` (create an .env file with this variable). Also you can acces to the bot's chat through the provided linK, in this case: t.me/enroute_reimburse_bot. 
3. Now your able to use your bot!

## 1.y Run tests
```bash
python -m unittest
```
Or with uv:
```bash
uv run python -m unittest
```

## 2. Connect Codex to an MCP server (Context7)
Context7 is a free MCP server for developer documentation.

```bash
codex mcp add context7 -- npx -y @upstash/context7-mcp
``` 


## 3. Agent architecture

### 3.1 Nodes
#### 2.1 Agent Plan
* **Role**: The brain (planner) 🧠
* **What it does**
    * Looks at:
        * user message
        * current state (what we already know)
    * Decides what to do next
    * Outputs a structured decision:
        * next_action
        * tool_args
        * optional message_to_user

* **Typical decisions**
    * “Extract receipt from files”
    * “Save expense to database”
    * “Query expense status”
    * “Ask the user for missing info”
    * “We’re done”

* Why it exists
> This is what makes the system agentic instead of a fixed flow.

#### 2.2 extract_receipt
* **Role**: Perception (Vision tool) 👁️
* **What it does**
    * Takes receipt images or PDFs
    * Calls a vision-capable model
    * Extracts structured fields:
        * merchant
        * date
        * total
        * currency
        * category
    * Outputs:
        * receipt_json
* **Why it exists**
> Separates seeing from thinking.

##### 2.3 upsert_expense
* **Role**: Action (Write to system of record) 🗄️
* **What it does**
    * Validates receipt data
    * Inserts or updates an expense record
    * Returns an expense_id
    * Outputs:
        * expense_id
* **Why it exists**
> This is the point where AI affects real business data.

#### 2.4 query_status
* **Role**: Memory retrieval (Read from DB) 🔎
* **What it does**
    * Queries the database for:
        * recent expenses
        * status (submitted, approved, rejected)
    * Applies optional filters from user message
    * Outputs:
        * status_rows
* **Why it exists**
> Agents don’t just create things — they answer questions.

#### 2.5 render_and_post
* **Role**: Communication layer 💬
* **What it does**
    * Converts agent state into a user-friendly response
    * Posts message to Telegram
* **Why it exists**
> UX belongs in one place, not spread across tools.

#### 2.6 END
* **Role**: Explicit termination
* **What it does**
    * Ends execution when:
        * the agent has asked the user for input
        * or the task is completed
* **Why it exists**
> Makes the lifecycle of the agent explicit and observable.

### Tools

#### Image Extractor
Extracts the contents of receipt as structured document.

* Test the tool:
```bash
uv run python src/tools/image_extractor.py --image-path images/receipts/invalid_receipt.jpg
```
* Expected output:
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
    },
    {
      "description": "Booking Fee",
      "quantity": 1.0,
      "unit_price": 24.66,
      "line_total": 24.66
    },
    {
      "description": "User Adjustment due to Labor Law",
      "quantity": 1.0,
      "unit_price": 6.34,
      "line_total": 6.34
    },
    {
      "description": "Discounts and Adjustments",
      "quantity": 1.0,
      "unit_price": -68.48,
      "line_total": -68.48
    }
  ]
}
```
