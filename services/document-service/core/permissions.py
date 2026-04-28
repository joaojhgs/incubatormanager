"""RBAC for document upload and download."""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from core.models import Document


class CanUploadDocuments(BasePermission):
    """Director and Staff may upload for any entity; Client only with a company context."""

    def has_permission(self, request: Request, view: object) -> bool:
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        role = getattr(user, "role", None)
        if role in ("Director", "Staff"):
            return True
        if role == "Client":
            return getattr(user, "company_id", None) is not None
        return False


class DocumentAccessPermission(BasePermission):
    """Object-level access to a stored :class:`~core.models.Document` record."""

    def has_permission(self, request: Request, view: object) -> bool:
        return bool(getattr(request.user, "is_authenticated", False))

    def has_object_permission(self, request: Request, view: object, obj: Document) -> bool:
        user = request.user
        role = getattr(user, "role", None)
        if role in ("Director", "Staff"):
            return True
        if role == "Client":
            company_id = getattr(user, "company_id", None)
            if company_id is None:
                return False
            if obj.entity_type == Document.EntityType.COMPANY:
                return str(obj.entity_id) == str(company_id)
            return False
        return False
