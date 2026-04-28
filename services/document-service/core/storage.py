"""MinIO storage adapter for document file operations.

Provides ``upload``, ``download``, ``delete`` and ``presigned_url`` helpers
that wrap the ``minio`` Python SDK.  All MinIO interaction is isolated here
so that the rest of the service stays decoupled from object-storage details.
"""

from __future__ import annotations

import io
import logging
import uuid
from typing import BinaryIO

from django.conf import settings
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


def _client() -> Minio:
    """Return a Minio client configured from Django settings / env vars."""
    s = settings.SHARED
    return Minio(
        s["MINIO_ENDPOINT"],
        access_key=s["MINIO_ACCESS_KEY"],
        secret_key=s["MINIO_SECRET_KEY"],
        secure=s["MINIO_USE_SSL"],
    )


def _bucket() -> str:
    """Return the configured bucket name."""
    return settings.SHARED["MINIO_BUCKET"] or "ilb-documents"


def _ensure_bucket(client: Minio, bucket: str) -> None:
    """Create the bucket if it does not already exist (idempotent)."""
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        logger.info("storage: created bucket %s", bucket)


def _object_path(entity_type: str, entity_id: uuid.UUID, filename: str) -> str:
    """Build the object key inside the bucket.

    Layout: ``<entity_type>/<entity_id>/<uuid>-<original_filename>``
    The leading UUID prevents name collisions when two uploads share the
    same original filename.
    """
    return f"{entity_type}/{entity_id}/{uuid.uuid4()}-{filename}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def upload(
    entity_type: str,
    entity_id: uuid.UUID,
    filename: str,
    data: BinaryIO,
    content_type: str,
    size: int,
) -> str:
    """Upload *data* to MinIO and return the object path (key).

    The caller is responsible for persisting the returned path in the
    ``Document.file_path`` field.
    """
    client = _client()
    bucket = _bucket()
    _ensure_bucket(client, bucket)
    object_name = _object_path(entity_type, entity_id, filename)
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=data,
        length=size,
        content_type=content_type,
    )
    logger.info("storage: uploaded %s/%s", bucket, object_name)
    return object_name


def download(file_path: str) -> tuple[io.BytesIO, str]:
    """Download an object from MinIO.

    Returns a ``(stream, content_type)`` tuple.  The caller should close the
    stream when done.
    """
    client = _client()
    bucket = _bucket()
    response = client.get_object(bucket_name=bucket, object_name=file_path)
    try:
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        buffer = io.BytesIO(response.read())
        buffer.seek(0)
    finally:
        response.close()
        response.release_conn()
    logger.info("storage: downloaded %s/%s", bucket, file_path)
    return buffer, content_type


def delete(file_path: str) -> None:
    """Remove an object from MinIO.  No-op if the object does not exist."""
    client = _client()
    bucket = _bucket()
    client.remove_object(bucket_name=bucket, object_name=file_path)
    logger.info("storage: deleted %s/%s", bucket, file_path)


def presigned_url(file_path: str, expires: int = 3600) -> str:
    """Return a pre-signed GET URL valid for *expires* seconds (default 1 h).

    The URL lets a client download the file directly from MinIO without
    going through the document-service, which is useful for large files.
    """
    from datetime import timedelta

    client = _client()
    bucket = _bucket()
    url = client.presigned_get_object(
        bucket_name=bucket,
        object_name=file_path,
        expires=timedelta(seconds=expires),
    )
    logger.info("storage: presigned URL generated for %s/%s", bucket, file_path)
    return url


class StorageError(Exception):
    """Raised when a MinIO operation fails."""


def safe_upload(
    entity_type: str,
    entity_id: uuid.UUID,
    filename: str,
    data: BinaryIO,
    content_type: str,
    size: int,
) -> str:
    """Upload wrapper that converts ``S3Error`` into ``StorageError``."""
    try:
        return upload(entity_type, entity_id, filename, data, content_type, size)
    except S3Error as exc:
        raise StorageError(f"MinIO upload failed: {exc}") from exc


def safe_download(file_path: str) -> tuple[io.BytesIO, str]:
    """Download wrapper that converts ``S3Error`` into ``StorageError``."""
    try:
        return download(file_path)
    except S3Error as exc:
        raise StorageError(f"MinIO download failed: {exc}") from exc


def safe_delete(file_path: str) -> None:
    """Delete wrapper that converts ``S3Error`` into ``StorageError``."""
    try:
        delete(file_path)
    except S3Error as exc:
        raise StorageError(f"MinIO delete failed: {exc}") from exc


def safe_presigned_url(file_path: str, expires: int = 3600) -> str:
    """Presigned-URL wrapper that converts ``S3Error`` into ``StorageError``."""
    try:
        return presigned_url(file_path, expires=expires)
    except S3Error as exc:
        raise StorageError(f"MinIO presigned URL failed: {exc}") from exc
