# AI Workshop Coding: Coding Assistant
## Before the workshop

- Prerequisites:
    - Python installed
    - Visual Studio Code (not mandatory)
    - Codex installed
    - OPENAI_API_KEY
    - Docker installed
- What’s already done?
    - Service skeleton
    - Schemas:
        - State
        - Receipt
        - AgentPlanResponse
    - Docker compose configuration
    - Tools
        - Image Extractor
    - Prompts:
        - Image Extractor
        - Agent Plan Response
    - [AGENTS.md](./AGENTS.md): guidelines for the coding assistant.

### What’s going to be done in the Workshop

1. Configure your own bot
2. Clone this repo: git clone -b workshop-feb-3 git@github.com:sergio-fernandez97/Enroute-ReimburseMate-TelegramBot.git
3. Connect your bot with your dummy app.
4. Show the [AGENTS.md](./AGENTS.md)
5. Show the workflow in a diagram. Take a screenshot and give it to codex in order to create the agent with LangGraph (empty nodes).
> [Image #1] Use Context7 to fetch the official LangGraph documentation. Look at the diagram in the image, which represents the workflow we want to build. Help me populate the nodes and include the graph in
src/graph/graph.py. Leave the logic of each node empty, we will work on that later.
> 
5.  Show the state: Pydantic model
**The information that is flowing through all the agent process.**
At `src/schemas/state.py`
```python
from typing import Any
from pydantic import BaseModel, Field

class WorkflowState(BaseModel):
    """Shared workflow state passed between nodes."""
    #### input from the chat ####
    user_input: str | None = Field(
        default=None,
        description="Raw user message text from the Telegram update.",
    )
    ###############################

    #### Telegram user data ####
    telegram_user_id: str | None = Field(
        default=None,
        description="Telegram user identifier for the requesting user.",
    )
    username: str | None = Field(
        default=None,
        description="Telegram username for the requesting user."
    )
    first_name: str | None = Field(
        default=None,
        description="Telegram first name for the requesting user."
    )
    last_name: str | None = Field(
        default=None,
        description="Telegram last name for the requesting user."
    )
    ###############################

    #### Reference for the file sent by the user ####
    file_id: str | None = Field(
        default=None,
        description="Telegram file_id associated with an uploaded receipt or document.",
    )
    ###############################

    #### Variables generated through the flow ####
    next_action: str | None = Field(
        default=None,
        description="Routing hint or node name for the next workflow step.",
    )
    receipt_json: dict[str, Any] | None = Field(
        default=None,
        description="Structured receipt data extracted from user input.",
    )
    expense_id: str | None = Field(
        default=None,
        description="Identifier for the created or matched expense record.",
    )
    status_rows: list[dict[str, Any]] | None = Field(
        default=None,
        description="Status rows from SQL DB used to build a response. Includes json non-serialisable types.",
    )
    response_text: str | None = Field(
        default=None,
        description="Final response text to send back to the user.",
    )
```
7. Validate the code of created: plot the graph in a notebook
> Use Context7 to fetch the official LangGraph documentation. And create a notebook named graph.ipynb. In one cell comile the graph (from src.graph.graph import graph) as "app". The plot the complete graph.
> 
8. Create the brain node (agent plan).

> Use Context7 to fetch the official LangGraph and LangChain documentation. And fill the node @src/nodes/agent_plan.py. Load the prompt in @src/prompts/agent_plan.md and create chain with the structured output in @src/schemas/agent_plan.py, then format the state in order to complete the prompt. Afterwards invoke the llm with structured output, extract the field next action and update the state
> 
9. With the multi agent functionality create the nodes: extract_receipt, query_status, render_and_post, upset_expense
    9.1 extract_receipt
    9.1.1 Test the tool.
    
    > Use Context7 to fetch the official LangGraph documentation. Fill the node @src/nodes/extract_receipt.py. Read the node description at @README.md. Then load the bytes of the image given the file_id in the state, call the tool for extracting the information from the file: @src/tools/images_extractor.py and then fill receipt_json with the information.
    > 
    9.2 query_status
    
    > Fill the node @src/nodes/query_status.py. Read the node description at @README.md. Load the prompt from @src/prompts/query_status.md and create a chain with the structured output given by @src/schemas/query_status.py, then include the user message in the request to the llm. Invoke the llm, extract the field queries if it is not null use the queries for retrieving the need information and fill the state field named status_rows.
    > 
    9.3 render_and_post
    
    > Fill the node @src/nodes/post_and_render.py. Read the node description at @README.md. Load the prompt from @src/prompts/post_and_render.md and create a chain with structured output given by @src/schemas/post_and_render.py, then include the current state in the request of the llm. Invoke the llm, extract the field response_text and update the state.
    > 
    9.4 upset_expense
    
    > Fill the node @src/nodes/upsert_expense.py. Read the node description at @README.md. Upsert  the needed information from state in sql tables and update state with expense_id.
    > 
10. Compile the graph in the app, use https://chatgpt.com/codex (not mandatory!):

> Import the graph from @src/graph/graph.py into @app.py and compile it. In @app.py modify the coroutines handle_text and handle_photo in order append the file and telegram user information to the state and then to invoke the graph. Afterwards extract the response from the workflow and return it to telegram.
>

11. Fix troubleshootings/bugs.
