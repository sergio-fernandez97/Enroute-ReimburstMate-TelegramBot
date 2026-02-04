import logging
import os
import tempfile
from pathlib import Path
from typing import Callable, Tuple

from src.schemas.state import WorkflowState
from src.tools.image_extractor import extract_receipt_from_image
from src.tools.minio_storage import get_minio_client


class ExtractReceipt:
    """Extracts structured receipt data from user input."""

    def __init__(
        self,
        downloads_dir: Path | None = None,
        extractor: Callable[..., object] | None = None,
    ) -> None:
        """Initialize the node.

        Args:
            downloads_dir: Directory to search for downloaded receipt files.
            extractor: Callable that extracts receipt data from an image path.
        """
        self._downloads_dir = downloads_dir or Path(__file__).resolve().parents[2] / "downloads"
        self._extractor = extractor or extract_receipt_from_image

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
        """Extract receipt data and update the workflow state."""
        if not state.file_id:
            logging.warning("ExtractReceipt missing file_id; skipping extraction.")
            return state

        image_bytes, suffix = self._load_file_bytes(state.file_id)
        if not image_bytes:
            logging.warning("ExtractReceipt could not load bytes for file_id=%s", state.file_id)
            return state

        receipt_json = self._extract_from_bytes(image_bytes, suffix)
        if receipt_json is None:
            logging.warning("ExtractReceipt returned no receipt data for file_id=%s", state.file_id)
            return state

        logging.info("ExtractReceipt completed for file_id=%s", state.file_id)
        return state.model_copy(update={"receipt_json": receipt_json})

    def _load_file_bytes(self, file_id: str) -> Tuple[bytes | None, str]:
        """Load receipt bytes for a given Telegram file_id.

        Args:
            file_id: Telegram file identifier or local file path.

        Returns:
            Tuple of (bytes, suffix) where suffix includes the leading dot.
        """
        local_path = self._resolve_local_path(file_id)
        if local_path:
            return local_path.read_bytes(), local_path.suffix or ".jpg"

        minio_bytes, minio_suffix = self._load_from_minio(file_id)
        if minio_bytes:
            return minio_bytes, minio_suffix

        return None, ".jpg"

    def _resolve_local_path(self, file_id: str) -> Path | None:
        """Resolve a local file path for the receipt if available."""
        candidate = Path(file_id)
        if candidate.is_file():
            return candidate

        if not self._downloads_dir.exists():
            return None

        matches = list(self._downloads_dir.glob(f"*{file_id}*"))
        if not matches:
            return None

        return max(matches, key=lambda path: path.stat().st_mtime)

    def _load_from_minio(self, file_id: str) -> Tuple[bytes | None, str]:
        """Load receipt bytes from MinIO using the file_id."""
        try:
            client, bucket = get_minio_client()
        except Exception as exc:
            logging.warning("MinIO not configured for receipt lookup: %s", exc)
            return None, ".jpg"

        try:
            objects = client.list_objects(bucket, prefix="telegram/", recursive=True)
            matching = [obj for obj in objects if file_id in obj.object_name]
        except Exception as exc:
            logging.warning("MinIO lookup failed for file_id=%s: %s", file_id, exc)
            return None, ".jpg"

        if not matching:
            return None, ".jpg"

        latest = max(matching, key=lambda obj: obj.last_modified or 0)
        suffix = Path(latest.object_name).suffix or ".jpg"

        try:
            response = client.get_object(bucket, latest.object_name)
            try:
                data = response.read()
            finally:
                response.close()
                response.release_conn()
        except Exception as exc:
            logging.warning("MinIO download failed for file_id=%s: %s", file_id, exc)
            return None, ".jpg"

        return data, suffix

    def _extract_from_bytes(self, image_bytes: bytes, suffix: str) -> dict | None:
        """Run the extractor tool on raw image bytes."""
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name

            result = self._extractor(image_path=temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        if hasattr(result, "model_dump"):
            return result.model_dump()
        if isinstance(result, dict):
            return result

        return None
