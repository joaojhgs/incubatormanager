"""Permission classes for ticket-service."""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from core.services import ticket_scope_for_user
from core.models import Ticket


class IsTicketOwnerOrStaff(BasePermission):
    """Allow access when request user owns the ticket or is Staff/Director."""

    def has_permission(self, request: Request, view: object) -> bool:
        role = getattr(request.user, "role", None)
        if role in {"Staff", "Director", "Client"}:
            return True
        return False

    def has_object_permission(self, request: Request, view: object, obj: Ticket) -> bool:
        role = getattr(request.user, "role", None)
        if role in {"Staff", "Director"}:
            return True

        if role != "Client":
            return False

        user_company = getattr(request.user, "company_id", None)
        return str(getattr(obj, "company_id", "")) == str(user_company)
