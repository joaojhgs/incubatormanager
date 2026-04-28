"""Tests for the MinIO storage adapter."""

from __future__ import annotations

import io
import os
import tempfile
import uuid
from unittest.mock import MagicMock, patch

import pytest
from core.storage import (
    StorageError,
    _object_path,
    delete,
    download,
    presigned_url,
    safe_delete,
    safe_download,
    safe_presigned_url,
    safe_upload,
    upload,
)

# ---------------------------------------------------------------------------
# _object_path
# ---------------------------------------------------------------------------


def test_object_path_includes_entity_type_and_id() -> None:
    entity_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    path = _object_path("Company", entity_id, "report.pdf")
    assert path.startswith("Company/12345678-1234-5678-1234-567812345678/")
    assert path.endswith("-report.pdf")


def test_object_path_unique_per_call() -> None:
    entity_id = uuid.uuid4()
    p1 = _object_path("Contract", entity_id, "doc.pdf")
    p2 = _object_path("Contract", entity_id, "doc.pdf")
    # The leading UUID makes each path unique
    assert p1 != p2


# ---------------------------------------------------------------------------
# upload
# ---------------------------------------------------------------------------


@pytest.fixture
def _minio_settings(settings) -> None:
    """Configure MinIO env vars for tests."""
    settings.SHARED["MINIO_ENDPOINT"] = "localhost:9000"
    settings.SHARED["MINIO_ACCESS_KEY"] = "minioadmin"
    settings.SHARED["MINIO_SECRET_KEY"] = "minioadmin"
    settings.SHARED["MINIO_BUCKET"] = "test-bucket"
    settings.SHARED["MINIO_USE_SSL"] = False


@patch("core.storage._client")
@patch("core.storage._ensure_bucket")
def test_upload_calls_put_object(
    mock_ensure: MagicMock,
    mock_client_fn: MagicMock,
    _minio_settings,
) -> None:
    mock_client = MagicMock()
    mock_client_fn.return_value = mock_client

    data = io.BytesIO(b"hello world")
    result = upload("Company", uuid.uuid4(), "test.txt", data, "text/plain", 11)

    mock_client.put_object.assert_called_once()
    assert result.startswith("Company/")


# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------


@patch("core.storage._client")
def test_download_returns_stream_and_content_type(
    mock_client_fn: MagicMock,
    _minio_settings,
) -> None:
    mock_client = MagicMock()
    mock_client_fn.return_value = mock_client

    fake_response = MagicMock()
    fake_response.headers = {"Content-Type": "application/pdf"}
    fake_response.read.return_value = b"%PDF-1.4 fake"
    fake_response.close = MagicMock()
    fake_response.release_conn = MagicMock()
    mock_client.get_object.return_value = fake_response

    buf, ct = download("Company/abc/test.pdf")
    assert ct == "application/pdf"
    assert buf.read() == b"%PDF-1.4 fake"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


@patch("core.storage._client")
def test_delete_calls_remove_object(
    mock_client_fn: MagicMock,
    _minio_settings,
) -> None:
    mock_client = MagicMock()
    mock_client_fn.return_value = mock_client

    delete("Company/abc/test.pdf")
    mock_client.remove_object.assert_called_once()


# ---------------------------------------------------------------------------
# presigned_url
# ---------------------------------------------------------------------------


@patch("core.storage._client")
def test_presigned_url_returns_url(
    mock_client_fn: MagicMock,
    _minio_settings,
) -> None:
    mock_client = MagicMock()
    mock_client_fn.return_value = mock_client
    mock_client.presigned_get_object.return_value = (
        "http://minio:9000/test-bucket/obj?signature=abc"
    )

    url = presigned_url("Company/abc/test.pdf")
    assert url.startswith("http")
    mock_client.presigned_get_object.assert_called_once()


# ---------------------------------------------------------------------------
# safe_* wrappers
# ---------------------------------------------------------------------------


@patch("core.storage.upload")
def test_safe_upload_raises_storage_error(
    mock_upload: MagicMock,
    _minio_settings,
) -> None:
    from minio.error import S3Error

    mock_upload.side_effect = S3Error(
        "NoSuchBucket",
        "The specified bucket does not exist",
        "resource",
        "request_id",
        "host_id",
        "response",
    )
    with pytest.raises(StorageError, match="MinIO upload failed"):
        safe_upload("Company", uuid.uuid4(), "f.txt", io.BytesIO(b""), "text/plain", 0)


@patch("core.storage.download")
def test_safe_download_raises_storage_error(
    mock_download: MagicMock,
    _minio_settings,
) -> None:
    from minio.error import S3Error

    mock_download.side_effect = S3Error(
        "NoSuchKey",
        "The specified key does not exist",
        "resource",
        "request_id",
        "host_id",
        "response",
    )
    with pytest.raises(StorageError, match="MinIO download failed"):
        safe_download("nonexistent/path")


@patch("core.storage.delete")
def test_safe_delete_raises_storage_error(
    mock_delete: MagicMock,
    _minio_settings,
) -> None:
    from minio.error import S3Error

    mock_delete.side_effect = S3Error(
        "AccessDenied", "Access Denied", "resource", "request_id", "host_id", "response"
    )
    with pytest.raises(StorageError, match="MinIO delete failed"):
        safe_delete("some/path")


@patch("core.storage.presigned_url")
def test_safe_presigned_url_raises_storage_error(
    mock_presigned: MagicMock,
    _minio_settings,
) -> None:
    from minio.error import S3Error

    mock_presigned.side_effect = S3Error(
        "AccessDenied", "Access Denied", "resource", "request_id", "host_id", "response"
    )
    with pytest.raises(StorageError, match="MinIO presigned URL failed"):
        safe_presigned_url("some/path")


# ---------------------------------------------------------------------------
# Round-trip (acceptance: tmp file through upload → download → delete)
# ---------------------------------------------------------------------------


@patch("core.storage._ensure_bucket")
@patch("core.storage._client")
def test_round_trip_upload_download_delete_uses_temp_file(
    mock_client_fn: MagicMock,
    mock_ensure: MagicMock,
    _minio_settings,
) -> None:
    """Mirror a real object lifecycle using on-disk bytes (tmp file)."""
    objects: dict[str, tuple[bytes, str]] = {}

    mock_client = MagicMock()

    def put_object(**kwargs: object) -> None:
        object_name = str(kwargs["object_name"])
        data = kwargs["data"]
        length = int(kwargs["length"])
        content_type = str(kwargs["content_type"])
        objects[object_name] = (data.read(length), content_type)

    def get_object(**kwargs: object) -> MagicMock:
        object_name = str(kwargs["object_name"])
        payload, ct = objects[object_name]
        fake_response = MagicMock()
        fake_response.headers = {"Content-Type": ct}
        fake_response.read.return_value = payload
        fake_response.close = MagicMock()
        fake_response.release_conn = MagicMock()
        return fake_response

    def remove_object(**kwargs: object) -> None:
        del objects[str(kwargs["object_name"])]

    mock_client.put_object.side_effect = put_object
    mock_client.get_object.side_effect = get_object
    mock_client.remove_object.side_effect = remove_object
    mock_client_fn.return_value = mock_client

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp.write(b"round-trip-payload")
        tmp.flush()
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as body:
            key = upload(
                "Company",
                uuid.uuid4(),
                "payload.bin",
                body,
                "application/octet-stream",
                len(b"round-trip-payload"),
            )
        buf, content_type = download(key)
        assert content_type == "application/octet-stream"
        assert buf.read() == b"round-trip-payload"
        delete(key)
        assert key not in objects
    finally:
        os.unlink(tmp_path)
