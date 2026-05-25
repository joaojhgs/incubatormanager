"""Ticket-local permissions."""

from __future__ import annotations

from rest_framework.permissions import BasePermission


class IsTicketOwnerOrStaff(BasePermission):
    """Allow staff/directors or the owning client company to access a ticket."""

    def has_object_permission(self, request, view, obj) -> bool:
        role = getattr(request.user, "role", None)
        if role in {"Staff", "Director"}:
            return True
        if role != "Client":
            return False
        return str(obj.company_id) == str(getattr(request.user, "company_id", ""))
