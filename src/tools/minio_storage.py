"""Helpers for storing files in MinIO."""

from __future__ import annotations

import logging
import os
from typing import Tuple
from urllib.parse import urlparse

from minio import Minio

logger = logging.getLogger(__name__)


def _parse_minio_endpoint(endpoint: str) -> Tuple[str, bool]:
    """Parse a MinIO endpoint into host and TLS flag.

    Args:
        endpoint: MinIO endpoint URL or host:port.

    Returns:
        Tuple of (host, secure).
    """
    if not endpoint:
        raise ValueError("MINIO_ENDPOINT is required")

    if "://" in endpoint:
        parsed = urlparse(endpoint)
        host = parsed.netloc or parsed.path
        secure = parsed.scheme == "https"
        return host, secure

    return endpoint, False


def get_minio_client() -> tuple[Minio, str]:
    """Create a MinIO client from environment variables.

    Returns:
        Tuple of (Minio client, bucket name).
    """
    endpoint = os.getenv("MINIO_ENDPOINT", "")
    access_key = os.getenv("MINIO_ACCESS_KEY", "")
    secret_key = os.getenv("MINIO_SECRET_KEY", "")
    bucket = os.getenv("MINIO_BUCKET", "")

    if not access_key or not secret_key or not bucket:
        raise ValueError("MINIO_ACCESS_KEY, MINIO_SECRET_KEY, and MINIO_BUCKET are required")

    host, secure = _parse_minio_endpoint(endpoint)

    client = Minio(
        host,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )
    return client, bucket


def ensure_bucket(client: Minio, bucket: str) -> None:
    """Ensure the bucket exists in MinIO.

    Args:
        client: MinIO client.
        bucket: Bucket name.
    """
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        logger.info("Created MinIO bucket: %s", bucket)


def upload_bytes(
    client: Minio,
    bucket: str,
    object_name: str,
    data: bytes,
    content_type: str,
    metadata: dict[str, str] | None = None,
) -> None:
    """Upload bytes to MinIO.

    Args:
        client: MinIO client.
        bucket: Bucket name.
        object_name: Object key in MinIO.
        data: Bytes to upload.
        content_type: MIME type.
    """
    from io import BytesIO

    ensure_bucket(client, bucket)
    stream = BytesIO(data)
    client.put_object(
        bucket,
        object_name,
        stream,
        length=len(data),
        content_type=content_type,
        metadata=metadata,
    )
