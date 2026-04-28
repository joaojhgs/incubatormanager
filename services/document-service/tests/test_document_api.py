"""HTTP tests for document upload and download."""

from __future__ import annotations

import io
import uuid
from unittest.mock import patch

import pytest
from core.models import Document
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient


def _auth_headers(
    *,
    user_id: uuid.UUID | None = None,
    role: str = "Staff",
    company_id: str | None = None,
) -> dict[str, str]:
    uid = str(user_id or uuid.uuid4())
    h: dict[str, str] = {
        "HTTP_X_USER_ID": uid,
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        h["HTTP_X_COMPANY_ID"] = company_id
    return h


@pytest.mark.django_db
def test_upload_staff_creates_metadata_and_calls_storage() -> None:
    company_id = uuid.uuid4()
    user_id = uuid.uuid4()
    key = f"Company/{company_id}/k-f.pdf"
    with patch("core.services.storage.safe_upload", return_value=key) as up:
        client = APIClient()
        pdf = SimpleUploadedFile("memo.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        resp = client.post(
            "/api/documents/upload/",
            {"file": pdf, "entity_type": "Company", "entity_id": str(company_id)},
            format="multipart",
            **_auth_headers(user_id=user_id),
        )
    assert resp.status_code == 201
    assert resp.data["file_name"] == "memo.pdf"
    assert resp.data["mime_type"] == "application/pdf"
    up.assert_called_once()
    doc = Document.objects.get(id=resp.data["id"])
    assert doc.uploaded_by == user_id


@pytest.mark.django_db
@patch("core.services.MAX_UPLOAD_BYTES", 100)
@patch("core.services.storage.safe_upload", return_value="Company/x/k.pdf")
def test_upload_rejects_over_max_bytes(_mock_upload: object) -> None:
    """Oversized bodies receive 413 (production cap is 20 MiB; lowered here for speed)."""
    company_id = uuid.uuid4()
    big = SimpleUploadedFile("big.pdf", b"x" * 101, content_type="application/pdf")
    client = APIClient()
    resp = client.post(
        "/api/documents/upload/",
        {"file": big, "entity_type": "Company", "entity_id": str(company_id)},
        format="multipart",
        **_auth_headers(),
    )
    assert resp.status_code == 413


@pytest.mark.django_db
def test_upload_rejects_disallowed_mime() -> None:
    company_id = uuid.uuid4()
    bad = SimpleUploadedFile("clip.mp4", b"\x00\x00\x00", content_type="video/mp4")
    client = APIClient()
    resp = client.post(
        "/api/documents/upload/",
        {"file": bad, "entity_type": "Company", "entity_id": str(company_id)},
        format="multipart",
        **_auth_headers(),
    )
    assert resp.status_code == 415


@pytest.mark.django_db
def test_upload_client_forbidden_for_foreign_company() -> None:
    mine = uuid.uuid4()
    other = uuid.uuid4()
    client = APIClient()
    pdf = SimpleUploadedFile("a.pdf", b"%PDF", content_type="application/pdf")
    resp = client.post(
        "/api/documents/upload/",
        {"file": pdf, "entity_type": "Company", "entity_id": str(other)},
        format="multipart",
        **_auth_headers(role="Client", company_id=str(mine)),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_upload_client_contract_entity_forbidden() -> None:
    company_id = uuid.uuid4()
    contract_id = uuid.uuid4()
    client = APIClient()
    pdf = SimpleUploadedFile("a.pdf", b"%PDF", content_type="application/pdf")
    resp = client.post(
        "/api/documents/upload/",
        {"file": pdf, "entity_type": "Contract", "entity_id": str(contract_id)},
        format="multipart",
        **_auth_headers(role="Client", company_id=str(company_id)),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_download_staff_streams_file() -> None:
    company_id = uuid.uuid4()
    doc = Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=company_id,
        file_name="out.pdf",
        file_path="Company/x/k.pdf",
        file_size=4,
        mime_type="application/pdf",
    )
    buf = io.BytesIO(b"%PDF")
    with patch("core.document_views.storage.safe_download", return_value=(buf, "application/pdf")):
        client = APIClient()
        resp = client.get(
            f"/api/documents/{doc.id}/download/",
            **_auth_headers(),
        )
    assert resp.status_code == 200
    body = b"".join(resp.streaming_content)
    assert body == b"%PDF"


@pytest.mark.django_db
def test_download_client_blocked_for_other_company_document() -> None:
    foreign_company = uuid.uuid4()
    doc = Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=foreign_company,
        file_name="secret.pdf",
        file_path="Company/x/s.pdf",
        file_size=1,
        mime_type="application/pdf",
    )
    client = APIClient()
    resp = client.get(
        f"/api/documents/{doc.id}/download/",
        **_auth_headers(role="Client", company_id=str(uuid.uuid4())),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_upload_without_gateway_headers_returns_401() -> None:
    client = APIClient()
    pdf = SimpleUploadedFile("a.pdf", b"%PDF", content_type="application/pdf")
    resp = client.post(
        "/api/documents/upload/",
        {"file": pdf, "entity_type": "Company", "entity_id": str(uuid.uuid4())},
        format="multipart",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_health_still_public() -> None:
    client = APIClient()
    resp = client.get("/api/documents/health/")
    assert resp.status_code == 200
