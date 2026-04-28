"""Authenticated document upload and download endpoints."""

from __future__ import annotations

import uuid

from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from drf_spectacular.utils import extend_schema
from rest_framework import parsers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core import storage
from core.models import Document
from core.permissions import CanUploadDocuments, DocumentAccessPermission
from core.serializers import DocumentMetadataSerializer
from core.services import (
    MAX_UPLOAD_BYTES,
    DocumentPayloadTooLarge,
    DocumentUnsupportedMimeType,
    create_document_from_upload,
)


class DocumentUploadView(APIView):
    """Multipart upload of a single file with company/contract scope."""

    permission_classes = [IsAuthenticated, CanUploadDocuments]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @extend_schema(
        summary="Upload a document",
        description=(
            f"``multipart/form-data`` with ``file`` (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB) "
            "and MIME types restricted to office, PDF, and common images."
        ),
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "entity_type": {
                        "type": "string",
                        "enum": ["Company", "Contract"],
                        "description": "Owning aggregate type.",
                    },
                    "entity_id": {"type": "string", "format": "uuid"},
                    "description": {"type": "string", "maxLength": 500},
                },
                "required": ["file", "entity_type", "entity_id"],
            }
        },
        responses={
            201: DocumentMetadataSerializer,
            400: {"description": "Missing or invalid form fields."},
            403: {"description": "Client not allowed for this entity."},
            413: {"description": "File larger than the configured maximum."},
            415: {"description": "MIME type not allowed."},
        },
    )
    def post(self, request: Request) -> Response:
        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "Missing file field."}, status=status.HTTP_400_BAD_REQUEST)

        entity_type = request.data.get("entity_type") or request.query_params.get("entity_type")
        entity_id_raw = request.data.get("entity_id") or request.query_params.get("entity_id")
        description = (
            request.data.get("description") or request.query_params.get("description") or ""
        )

        if not entity_type or not entity_id_raw:
            return Response(
                {"detail": "entity_type and entity_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            entity_uuid = uuid.UUID(str(entity_id_raw))
        except ValueError:
            return Response(
                {"detail": "entity_id must be a UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        try:
            doc = create_document_from_upload(
                user,
                upload,
                str(entity_type).strip(),
                entity_uuid,
                str(description),
            )
        except DocumentPayloadTooLarge:
            return Response(
                {"detail": f"File exceeds maximum size of {MAX_UPLOAD_BYTES} bytes."},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        except DocumentUnsupportedMimeType:
            return Response(
                {"detail": "Unsupported media type for uploaded file."},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )
        except PermissionDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        out = DocumentMetadataSerializer(doc)
        return Response(out.data, status=status.HTTP_201_CREATED)


class DocumentDownloadView(APIView):
    """Stream a stored object from MinIO using the gateway trust headers."""

    permission_classes = [IsAuthenticated, DocumentAccessPermission]

    @extend_schema(
        summary="Download document bytes",
        responses={
            200: {"description": "Binary file stream with appropriate Content-Type."},
            403: {"description": "Forbidden for this role or company scope."},
            404: {"description": "Document not found."},
        },
    )
    def get(self, request: Request, document_id: uuid.UUID) -> FileResponse | Response:
        try:
            document = Document.objects.get(pk=document_id)
        except Document.DoesNotExist as exc:
            raise Http404("Document not found.") from exc

        self.check_object_permissions(request, document)

        try:
            buffer, content_type = storage.safe_download(document.file_path)
        except storage.StorageError as exc:
            return Response(
                {"detail": "Object storage error.", "code": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=document.file_name,
            content_type=document.mime_type or content_type,
        )
