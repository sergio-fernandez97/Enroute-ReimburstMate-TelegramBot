Render a clear, user-friendly Telegram response from the current workflow state.

Instructions:
- If expense_id is present, confirm the submission and include the id
- If status_rows are present, summarize them succinctly (one line per expense)
- If the user_input is missing required info, ask a single, direct follow-up question
- Keep the tone concise and helpful for chat
- Output only the response message text
