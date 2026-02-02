Analyze the current workflow state and choose the next action for the reimbursement workflow.

Instructions:
- Use only one of these actions: extract_receipt, upsert_expense, query_status, render_and_post.
- If there is a receipt file_id and no receipt_json yet, choose extract_receipt.
- If receipt_json is present and expense_id is missing, choose upsert_expense.
- If the user_input is asking for status or history, choose query_status.
- If the user_input is asking for status or history, but status_rows is not None, choose render_and_post.
- In any other case choose render_and_post.
