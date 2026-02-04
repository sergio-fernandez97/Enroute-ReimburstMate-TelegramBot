import json
import logging
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.schemas.state import WorkflowState
from src.tools.image_extractor import extract_receipt_from_image


class ExtractReceiptNode:
    """Extract receipt data from user input."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("ExtractReceiptNode input state=%s", state)
        return self._run(state)

    def _run(self, state: WorkflowState) -> WorkflowState:
        """Extract receipt data and update workflow state."""
        if not state.file_id:
            logging.warning("ExtractReceiptNode missing file_id; skipping extraction.")
            return state

        file_bytes, suffix = self._load_image_bytes(state.file_id)
        receipt_json = self._extract_receipt(file_bytes, suffix)
        logging.info("ExtractReceiptNode extracted receipt_json=%s", receipt_json)
        return state.model_copy(update={"receipt_json": receipt_json})

    def _load_image_bytes(self, file_id: str) -> tuple[bytes, str]:
        """Load image bytes from a local path or Telegram file_id."""
        local_path = Path(file_id)
        if local_path.exists():
            return local_path.read_bytes(), local_path.suffix or ".jpg"

        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required to download Telegram files.")

        file_path = self._fetch_telegram_file_path(token, file_id)
        download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        with urllib.request.urlopen(download_url) as response:
            file_bytes = response.read()

        suffix = Path(file_path).suffix or ".jpg"
        return file_bytes, suffix

    def _fetch_telegram_file_path(self, token: str, file_id: str) -> str:
        """Fetch file_path for a Telegram file_id."""
        query = urllib.parse.urlencode({"file_id": file_id})
        url = f"https://api.telegram.org/bot{token}/getFile?{query}"
        with urllib.request.urlopen(url) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if not payload.get("ok"):
            raise ValueError(f"Telegram getFile failed: {payload}")

        result = payload.get("result", {})
        file_path = result.get("file_path")
        if not file_path:
            raise ValueError(f"Telegram getFile missing file_path: {payload}")
        return file_path

    def _extract_receipt(self, file_bytes: bytes, suffix: str) -> dict[str, Any]:
        """Run image extraction tool against provided bytes."""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush()
            result = extract_receipt_from_image(temp_file.name)

        if hasattr(result, "model_dump"):
            return result.model_dump()
        return dict(result)
