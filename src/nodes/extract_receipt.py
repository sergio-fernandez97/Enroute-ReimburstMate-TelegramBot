import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Optional, Tuple

from src.schemas.state import WorkflowState
from src.tools.images_extractor import extract_receipt_from_image
from src.tools.minio_storage import get_minio_client


class ExtractReceipt:
    """Extract receipt data from user-provided files or text."""

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
        """Extract receipt data from a stored image and update the state."""
        if not state.file_id:
            logging.info("ExtractReceipt skipped: no file_id in state.")
            return state

        image_bytes, suffix, image_path = self._load_image_bytes(state.file_id)
        if not image_bytes:
            logging.warning("ExtractReceipt skipped: could not resolve bytes for file_id=%s", state.file_id)
            return state

        receipt_json = self._extract_receipt_json(image_bytes, suffix, image_path)
        return state.model_copy(update={"receipt_json": receipt_json})

    def _extract_receipt_json(
        self,
        image_bytes: bytes,
        suffix: str,
        image_path: Optional[Path],
    ) -> dict[str, Any]:
        """Run the image extractor tool and return receipt JSON."""
        if image_path:
            result = extract_receipt_from_image(str(image_path))
            return self._normalize_result(result)

        temp_path = self._write_temp_image(image_bytes, suffix)
        try:
            result = extract_receipt_from_image(str(temp_path))
            return self._normalize_result(result)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                logging.warning("Failed to remove temp image: %s", temp_path)

    def _normalize_result(self, result: Any) -> dict[str, Any]:
        """Normalize extractor output into a JSON-serializable dict."""
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if isinstance(result, dict):
            return result
        return {"raw_result": result}

    def _write_temp_image(self, image_bytes: bytes, suffix: str) -> str:
        """Persist bytes to a temporary image file for the extractor."""
        suffix = suffix or ".jpg"
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(image_bytes)
            return tmp_file.name

    def _load_image_bytes(
        self, file_id: str
    ) -> Tuple[Optional[bytes], str, Optional[Path]]:
        """Load image bytes from local storage or MinIO."""
        local_path = self._resolve_local_path(file_id)
        if local_path:
            return local_path.read_bytes(), local_path.suffix or ".jpg", local_path

        minio_payload = self._fetch_from_minio(file_id)
        if minio_payload:
            image_bytes, suffix = minio_payload
            return image_bytes, suffix, None

        return None, "", None

    def _resolve_local_path(self, file_id: str) -> Optional[Path]:
        """Locate a file locally by file_id or filename match."""
        candidate = Path(file_id)
        if candidate.exists() and candidate.is_file():
            return candidate

        repo_root = Path(__file__).resolve().parents[2]
        search_roots = [repo_root / "downloads", repo_root / "images"]
        for root in search_roots:
            if not root.exists():
                continue
            for match in root.rglob(f"*{file_id}*"):
                if match.is_file():
                    return match
        return None

    def _fetch_from_minio(self, file_id: str) -> Optional[Tuple[bytes, str]]:
        """Fetch bytes from MinIO if configured."""
        try:
            client, bucket = get_minio_client()
        except Exception as exc:
            logging.info("MinIO not configured or unavailable: %s", exc)
            return None

        for obj in client.list_objects(bucket, prefix="telegram/", recursive=True):
            if file_id not in obj.object_name:
                continue
            response = client.get_object(bucket, obj.object_name)
            try:
                data = response.read()
            finally:
                response.close()
                response.release_conn()
            suffix = Path(obj.object_name).suffix or ".jpg"
            return data, suffix
        return None
