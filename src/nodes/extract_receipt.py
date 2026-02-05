import logging
import os
import tempfile
from pathlib import Path

from src.schemas.state import WorkflowState
from src.tools.image_extractor import extract_receipt_from_image
from src.tools.minio_storage import get_minio_client


class ExtractReceipt:
    """Extract receipt data from user input or files."""

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Run the node.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        logging.info("ExtractReceipt input state=%s", state)
        return self._extract(state)

    def _extract(self, state: WorkflowState) -> WorkflowState:
        """Parse and extract receipt data into state."""
        if state.receipt_json is not None:
            return state
        if not state.file_id:
            return state

        image_payload = self._load_image_bytes(state)
        if not image_payload:
            return state

        image_bytes, suffix = image_payload
        receipt_json = self._extract_receipt_json(image_bytes, suffix)
        if receipt_json is None:
            return state

        return state.model_copy(update={"receipt_json": receipt_json})

    def _load_image_bytes(self, state: WorkflowState) -> tuple[bytes, str] | None:
        """Load image bytes from disk or MinIO based on the file_id."""
        file_id = state.file_id
        local_path = self._find_local_file(file_id)
        if local_path:
            return local_path.read_bytes(), local_path.suffix or ".jpg"

        try:
            client, bucket = get_minio_client()
        except ValueError as exc:
            logging.warning("MinIO not configured for receipt lookup: %s", exc)
            return None

        object_name = self._find_minio_object_name(client, bucket, file_id, state.telegram_user_id)
        if not object_name:
            logging.warning("No MinIO object found for file_id=%s", file_id)
            return None

        response = client.get_object(bucket, object_name)
        try:
            data = response.read()
        finally:
            response.close()
            response.release_conn()

        return data, Path(object_name).suffix or ".jpg"

    def _find_local_file(self, file_id: str) -> Path | None:
        """Resolve a local file path when file_id maps to a local path."""
        if not file_id:
            return None
        candidate = Path(file_id)
        if candidate.exists():
            return candidate
        downloads_dir = Path(__file__).resolve().parents[2] / "downloads"
        if downloads_dir.exists():
            for path in downloads_dir.iterdir():
                if file_id in path.name:
                    return path
        return None

    def _find_minio_object_name(
        self,
        client,
        bucket: str,
        file_id: str,
        telegram_user_id: str | None,
    ) -> str | None:
        """Locate a MinIO object name that contains the Telegram file_id."""
        if not file_id:
            return None
        prefixes = []
        if telegram_user_id:
            prefixes.append(f"telegram/{telegram_user_id}/")
        prefixes.append("telegram/")

        for prefix in prefixes:
            for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
                if file_id in obj.object_name:
                    return obj.object_name
        return None

    def _extract_receipt_json(self, image_bytes: bytes, suffix: str) -> dict | None:
        """Run the image extractor tool and normalize the result."""
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name

            result = extract_receipt_from_image(temp_path)
            return self._normalize_receipt_result(result)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def _normalize_receipt_result(self, result) -> dict | None:
        """Normalize extractor result to a plain dict."""
        if result is None:
            return None
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if isinstance(result, dict):
            return result
        return {"raw": str(result)}
