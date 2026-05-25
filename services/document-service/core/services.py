"""Document upload, download, list, and delete business rules."""

from __future__ import annotations

import logging
import uuid
from typing import BinaryIO

from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import QuerySet
from ilb_common.permissions import RequestUser

from core import storage
from core.models import Document

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024

ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
)


class DocumentPayloadTooLarge(Exception):
    """Raised when the uploaded file exceeds ``MAX_UPLOAD_BYTES``."""


class DocumentUnsupportedMimeType(Exception):
    """Raised when ``Content-Type`` is not in ``ALLOWED_CONTENT_TYPES``."""


def _normalize_content_type(raw: str | None) -> str:
    if not raw:
        return ""
    return raw.split(";", 1)[0].strip().lower()


def _assert_upload_allowed_for_client(
    user: RequestUser,
    entity_type: str,
    entity_id: uuid.UUID,
) -> None:
    if user.role != "Client":
        return
    if user.company_id is None:
        raise PermissionDenied("Client uploads require a company context.")
    if entity_type != Document.EntityType.COMPANY:
        raise PermissionDenied("Clients may only upload documents for a company they belong to.")
    if str(entity_id) != str(user.company_id):
        raise PermissionDenied("Entity does not match the authenticated client's company.")


def create_document_from_upload(
    user: RequestUser,
    upload_file: UploadedFile,
    entity_type: str,
    entity_id: uuid.UUID,
    description: str,
) -> Document:
    """Validate size/MIME/RBAC, persist to MinIO, and create a ``Document`` row."""
    size = int(upload_file.size)
    if size > MAX_UPLOAD_BYTES:
        raise DocumentPayloadTooLarge()

    content_type = _normalize_content_type(upload_file.content_type)
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise DocumentUnsupportedMimeType()

    if entity_type not in {
        Document.EntityType.COMPANY,
        Document.EntityType.CONTRACT,
        Document.EntityType.BOOKING,
    }:
        msg = "entity_type must be Company, Contract, or Booking."
        raise ValueError(msg)

    _assert_upload_allowed_for_client(user, entity_type, entity_id)

    original_name = upload_file.name or "upload.bin"
    file_stream: BinaryIO = upload_file.file
    file_stream.seek(0)

    object_key = storage.safe_upload(
        entity_type,
        entity_id,
        original_name,
        file_stream,
        content_type,
        size,
    )

    doc = Document.objects.create(
        entity_type=entity_type,
        entity_id=entity_id,
        file_name=original_name,
        file_path=object_key,
        file_size=size,
        mime_type=content_type,
        description=description[:500] if description else "",
        uploaded_by=user.id,
    )
    logger.info("document created id=%s entity=%s/%s", doc.id, entity_type, entity_id)
    return doc


def documents_for_list_request(
    user: RequestUser,
    entity_type: str,
    entity_id: uuid.UUID,
) -> QuerySet[Document]:
    """Return active documents for the entity, enforcing list RBAC for Clients."""
    if entity_type not in {
        Document.EntityType.COMPANY,
        Document.EntityType.CONTRACT,
        Document.EntityType.BOOKING,
    }:
        msg = "entity_type must be Company, Contract, or Booking."
        raise ValueError(msg)

    qs: QuerySet[Document] = Document.objects.filter(
        is_active=True,
        entity_type=entity_type,
        entity_id=entity_id,
    ).order_by("-uploaded_at")

    if user.role in ("Director", "Staff"):
        return qs
    if user.role == "Client":
        if user.company_id is None:
            raise PermissionDenied("Client listing requires a company context.")
        if entity_type != Document.EntityType.COMPANY:
            raise PermissionDenied("Clients may only list documents for a company they belong to.")
        if str(entity_id) != str(user.company_id):
            raise PermissionDenied("Entity does not match the authenticated client's company.")
        return qs
    raise PermissionDenied("Unsupported role for document listing.")


def soft_delete_document(*, document: Document) -> None:
    """Mark the row inactive and remove the MinIO object after commit."""
    file_path = document.file_path
    pk = document.pk

    with transaction.atomic():
        doc = Document.objects.select_for_update().get(pk=pk, is_active=True)
        doc.is_active = False
        doc.save(update_fields=["is_active"])
    try:
        storage.safe_delete(file_path)
    except storage.StorageError as exc:
        logger.warning(
            "MinIO delete failed after soft-delete document id=%s path=%s: %s",
            pk,
            file_path,
            exc,
        )
    logger.info("document soft-deleted id=%s", pk)
