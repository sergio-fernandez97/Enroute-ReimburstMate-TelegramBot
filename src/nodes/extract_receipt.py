import logging
import os
import tempfile
from typing import Any, Tuple

from src.tools.image_extractor import extract_receipt_from_image
from src.tools.minio_storage import ensure_bucket, get_minio_client

from src.schemas.state import WorkflowState


class ExtractReceipt:
    """Extracts structured data from receipt images."""

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
        """Extract receipt data from the stored image bytes."""
        if not state.file_id:
            logging.info("ExtractReceipt skipping: missing file_id")
            return state
        if state.receipt_json is not None:
            logging.info("ExtractReceipt skipping: receipt_json already present")
            return state

        image_bytes, suffix = self._load_image_bytes(state)
        receipt_data = self._run_extractor(image_bytes, suffix)
        return state.model_copy(update={"receipt_json": receipt_data})

    def _load_image_bytes(self, state: WorkflowState) -> Tuple[bytes, str]:
        """Load image bytes for the provided file_id.

        Args:
            state: Current workflow state.

        Returns:
            Tuple of (image bytes, file suffix).
        """
        file_id = state.file_id or ""
        if os.path.exists(file_id):
            suffix = os.path.splitext(file_id)[1] or ".jpg"
            with open(file_id, "rb") as handle:
                return handle.read(), suffix

        return self._load_from_minio(file_id)

    def _load_from_minio(self, file_id: str) -> Tuple[bytes, str]:
        """Load image bytes from MinIO by file_id metadata."""
        client, bucket = get_minio_client()
        ensure_bucket(client, bucket)
        prefix = os.environ.get("MINIO_PREFIX", "telegram/")
        for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
            stat = client.stat_object(bucket, obj.object_name)
            metadata = {key.lower(): value for key, value in (stat.metadata or {}).items()}
            stored_id = metadata.get("x-amz-meta-file_id") or metadata.get("file_id")
            if stored_id != file_id:
                continue

            response = client.get_object(bucket, obj.object_name)
            try:
                data = response.read()
            finally:
                response.close()
                response.release_conn()

            suffix = os.path.splitext(obj.object_name)[1] or ".jpg"
            return data, suffix

        raise FileNotFoundError(f"Unable to locate file_id={file_id} in MinIO")

    def _run_extractor(self, image_bytes: bytes, suffix: str) -> dict[str, Any]:
        """Run the receipt extraction tool on the image bytes."""
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                handle.write(image_bytes)
                tmp_path = handle.name

            result = extract_receipt_from_image(tmp_path, model=model)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        if hasattr(result, "model_dump"):
            return result.model_dump()
        if isinstance(result, dict):
            return result
        return {"result": result}
