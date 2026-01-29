# AGENTS.md

Guidelines for coding agents working in this repository during a workshop that demonstrates Codex capabilities.

## Workshop orientation
- Goal: showcase Codex as a collaborative coding agent while building a Telegram bot service powered by a LangGraph AI workflow.
- Audience: workshop participants who want to see reasoning, tooling, and safe iteration in action.
- Emphasis: clear, incremental progress, visible checkpoints, and explainable decisions.

## Project context
- Repo purpose: Enroute ReimburstMate Telegram Bot service.
- Core idea: wire a Telegram bot to a LangGraph workflow that orchestrates AI steps.
- Tech stack: Python (see `pyproject.toml`, `app.py`, `main.py`).
- Default shell: zsh.

## How to work (Codex demo style)
- Prefer small, focused changes; narrate intent and outcome succinctly.
- Before edits: read relevant files and cite where changes will go.
- After edits: summarize what changed and why it matters for the demo.
- Keep code Pythonic and consistent with current style; add only minimal, high‑value comments.
- Avoid introducing new dependencies unless requested; if needed, explain tradeoffs.

## Coding Guidelines
* **File naming (nodes)**
    * Use snake_case for node files.
    * A node named "DB Handler" must be saved as `src/nodes/db_handler.py`.
* **Where to put files**
    * Place node implementations in `src/nodes/`.
* **Style**
    * Follow PEP 8.
    * Use Google Style docstrings.
* **Node structure**
    * Every node must be a class with `__call__(self, state, config)`.
    * Log the state at the start of each node to keep visibility on every input.
    * Keep `__call__` short; move work into submethods and call them inside `__call__`.
* **Example**
    ```python
    import logging

    class DbHandler:
        """Handles database read/write for expenses."""

        def __call__(self, state, config):
            """Run the node.

            Args:
                state: Current workflow state.
                config: Node configuration.

            Returns:
                Updated workflow state.
            """
            logging.info("DbHandler input state=%s", state)
            expense = self._normalize(state)
            return self._persist(expense, config)

        def _normalize(self, state):
            """Normalize incoming state into an expense object."""
            return state

        def _persist(self, expense, config):
            """Write the expense and return updated state."""
            return expense
    ```

## Demo checkpoints
- Bootstrapping: locate entry points and current bot wiring.
- Workflow: implement or connect LangGraph nodes/edges with clear step names.
- Telegram integration: keep handlers simple and show how user input flows into the graph.
- Observability: add lightweight logs or prints that make the workflow visible in a demo.

## Commands
- Prefer `rg` for search.
- If you need to run tests or install/upgrade dependencies, ask first.

## Safety
- Do not run destructive commands (e.g., `rm -rf`, `git reset --hard`) unless explicitly requested.
- Never commit changes unless asked.

## Ask when unsure
- If requirements are ambiguous, ask a brief clarifying question before proceeding.
