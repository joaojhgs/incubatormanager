"""HTTP tests for document upload, download, list, and delete."""

from __future__ import annotations

import io
import uuid
from unittest.mock import patch

import pytest
from core.models import Document
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
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
    assert resp.data["download_url"].endswith(f"/api/documents/{resp.data['id']}/download/")
    up.assert_called_once()
    doc = Document.objects.get(id=resp.data["id"])
    assert doc.uploaded_by == user_id


@pytest.mark.django_db
def test_upload_client_own_company_creates_metadata_and_can_list() -> None:
    company_id = uuid.uuid4()
    key = f"Company/{company_id}/client-note.pdf"
    with patch("core.services.storage.safe_upload", return_value=key):
        client = APIClient()
        pdf = SimpleUploadedFile("client-note.pdf", b"%PDF", content_type="application/pdf")
        upload = client.post(
            "/api/documents/upload/",
            {"file": pdf, "entity_type": "Company", "entity_id": str(company_id)},
            format="multipart",
            **_auth_headers(role="Client", company_id=str(company_id)),
        )
    assert upload.status_code == 201
    assert upload.data["entity_type"] == Document.EntityType.COMPANY

    listed = APIClient().get(
        f"/api/documents/?entity_type=Company&entity_id={company_id}",
        **_auth_headers(role="Client", company_id=str(company_id)),
    )

    assert listed.status_code == 200
    assert [row["id"] for row in listed.data] == [upload.data["id"]]
    assert listed.data[0]["download_url"].endswith(f"/api/documents/{upload.data['id']}/download/")


@pytest.mark.django_db
def test_upload_staff_booking_document_can_list() -> None:
    booking_id = uuid.uuid4()
    key = f"Booking/{booking_id}/agenda.pdf"
    with patch("core.services.storage.safe_upload", return_value=key):
        client = APIClient()
        pdf = SimpleUploadedFile("agenda.pdf", b"%PDF", content_type="application/pdf")
        upload = client.post(
            "/api/documents/upload/",
            {"file": pdf, "entity_type": "Booking", "entity_id": str(booking_id)},
            format="multipart",
            **_auth_headers(),
        )
    assert upload.status_code == 201
    assert upload.data["entity_type"] == Document.EntityType.BOOKING

    listed = APIClient().get(
        f"/api/documents/?entity_type=Booking&entity_id={booking_id}",
        **_auth_headers(),
    )

    assert listed.status_code == 200
    assert [row["file_name"] for row in listed.data] == ["agenda.pdf"]


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
def test_upload_client_booking_entity_forbidden() -> None:
    company_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    client = APIClient()
    pdf = SimpleUploadedFile("a.pdf", b"%PDF", content_type="application/pdf")
    resp = client.post(
        "/api/documents/upload/",
        {"file": pdf, "entity_type": "Booking", "entity_id": str(booking_id)},
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
    with patch(
        "core.document_views.storage.safe_download",
        return_value=(buf, "application/pdf"),
    ):
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


@pytest.mark.django_db
def test_list_staff_returns_only_active_documents() -> None:
    company_id = uuid.uuid4()
    Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=company_id,
        file_name="active.pdf",
        file_path="Company/x/active.pdf",
        file_size=1,
        mime_type="application/pdf",
        is_active=True,
    )
    Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=company_id,
        file_name="gone.pdf",
        file_path="Company/x/gone.pdf",
        file_size=2,
        mime_type="application/pdf",
        is_active=False,
    )
    client = APIClient()
    resp = client.get(
        f"/api/documents/?entity_type=Company&entity_id={company_id}",
        **_auth_headers(),
    )
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["file_name"] == "active.pdf"


@pytest.mark.django_db
def test_list_staff_query_count_bounded() -> None:
    company_id = uuid.uuid4()
    for i in range(3):
        Document.objects.create(
            entity_type=Document.EntityType.COMPANY,
            entity_id=company_id,
            file_name=f"f{i}.pdf",
            file_path=f"Company/x/{i}.pdf",
            file_size=1,
            mime_type="application/pdf",
        )
    client = APIClient()
    with CaptureQueriesContext(connection) as ctx:
        resp = client.get(
            f"/api/documents/?entity_type=Company&entity_id={company_id}",
            **_auth_headers(),
        )
    assert resp.status_code == 200
    assert len(resp.data) == 3
    assert len(ctx.captured_queries) <= 8


@pytest.mark.django_db
def test_list_missing_query_params_returns_400() -> None:
    client = APIClient()
    resp = client.get("/api/documents/", **_auth_headers())
    assert resp.status_code == 400


@pytest.mark.django_db
def test_list_invalid_entity_id_uuid_returns_400() -> None:
    client = APIClient()
    resp = client.get(
        "/api/documents/?entity_type=Company&entity_id=not-a-uuid",
        **_auth_headers(),
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_list_client_allowed_for_own_company() -> None:
    company_id = uuid.uuid4()
    Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=company_id,
        file_name="mine.pdf",
        file_path="Company/x/m.pdf",
        file_size=1,
        mime_type="application/pdf",
    )
    client = APIClient()
    resp = client.get(
        f"/api/documents/?entity_type=Company&entity_id={company_id}",
        **_auth_headers(role="Client", company_id=str(company_id)),
    )
    assert resp.status_code == 200
    assert len(resp.data) == 1


@pytest.mark.django_db
def test_list_client_forbidden_wrong_company_entity() -> None:
    company_id = uuid.uuid4()
    other = uuid.uuid4()
    Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=other,
        file_name="other.pdf",
        file_path="Company/x/o.pdf",
        file_size=1,
        mime_type="application/pdf",
    )
    client = APIClient()
    resp = client.get(
        f"/api/documents/?entity_type=Company&entity_id={other}",
        **_auth_headers(role="Client", company_id=str(company_id)),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_list_client_forbidden_contract_entity() -> None:
    contract_id = uuid.uuid4()
    company_id = uuid.uuid4()
    Document.objects.create(
        entity_type=Document.EntityType.CONTRACT,
        entity_id=contract_id,
        file_name="c.pdf",
        file_path="Contract/x/c.pdf",
        file_size=1,
        mime_type="application/pdf",
    )
    client = APIClient()
    resp = client.get(
        f"/api/documents/?entity_type=Contract&entity_id={contract_id}",
        **_auth_headers(role="Client", company_id=str(company_id)),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_delete_staff_soft_deletes_and_calls_minio() -> None:
    company_id = uuid.uuid4()
    doc = Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=company_id,
        file_name="d.pdf",
        file_path="Company/x/d.pdf",
        file_size=1,
        mime_type="application/pdf",
    )
    with patch("core.services.storage.safe_delete") as rm:
        client = APIClient()
        resp = client.delete(f"/api/documents/{doc.id}/", **_auth_headers())
    assert resp.status_code == 204
    rm.assert_called_once_with("Company/x/d.pdf")
    doc.refresh_from_db()
    assert doc.is_active is False


@pytest.mark.django_db
def test_delete_client_returns_403() -> None:
    company_id = uuid.uuid4()
    doc = Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=company_id,
        file_name="d.pdf",
        file_path="Company/x/d.pdf",
        file_size=1,
        mime_type="application/pdf",
    )
    client = APIClient()
    resp = client.delete(
        f"/api/documents/{doc.id}/",
        **_auth_headers(role="Client", company_id=str(company_id)),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_delete_unknown_id_returns_404() -> None:
    client = APIClient()
    resp = client.delete(f"/api/documents/{uuid.uuid4()}/", **_auth_headers())
    assert resp.status_code == 404


@pytest.mark.django_db
def test_download_soft_deleted_returns_404() -> None:
    company_id = uuid.uuid4()
    doc = Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=company_id,
        file_name="gone.pdf",
        file_path="Company/x/g.pdf",
        file_size=1,
        mime_type="application/pdf",
        is_active=False,
    )
    client = APIClient()
    resp = client.get(f"/api/documents/{doc.id}/download/", **_auth_headers())
    assert resp.status_code == 404


@pytest.mark.django_db
def test_download_unknown_id_returns_404() -> None:
    client = APIClient()
    resp = client.get(f"/api/documents/{uuid.uuid4()}/download/", **_auth_headers())
    assert resp.status_code == 404


@pytest.mark.django_db
def test_presigned_url_returns_metadata_for_staff() -> None:
    company_id = uuid.uuid4()
    doc = Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=company_id,
        file_name="signed.pdf",
        file_path="Company/x/signed.pdf",
        file_size=1,
        mime_type="application/pdf",
    )
    with patch(
        "core.document_views.storage.safe_presigned_url",
        return_value="https://minio.local/signed",
    ) as presign:
        client = APIClient()
        resp = client.get(f"/api/documents/{doc.id}/presigned/", **_auth_headers())

    assert resp.status_code == 200
    assert resp.data["id"] == str(doc.id)
    assert resp.data["presigned_url"] == "https://minio.local/signed"
    assert resp.data["download_url"].endswith(f"/api/documents/{doc.id}/download/")
    presign.assert_called_once_with("Company/x/signed.pdf")


@pytest.mark.django_db
def test_presigned_url_client_forbidden_for_contract_document() -> None:
    contract_id = uuid.uuid4()
    doc = Document.objects.create(
        entity_type=Document.EntityType.CONTRACT,
        entity_id=contract_id,
        file_name="contract.pdf",
        file_path="Contract/x/c.pdf",
        file_size=1,
        mime_type="application/pdf",
    )
    client = APIClient()
    resp = client.get(
        f"/api/documents/{doc.id}/presigned/",
        **_auth_headers(role="Client", company_id=str(uuid.uuid4())),
    )
    assert resp.status_code == 403
