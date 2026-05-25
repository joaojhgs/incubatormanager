"""Service helpers for ticket-service."""

from __future__ import annotations

from core.models import Ticket


def ticket_scope_for_user(user: object) -> list:
    """Return a role-scoped queryset for ticket listing and access."""

    role = getattr(user, "role", None)
    if role in {"Staff", "Director"}:
        return Ticket.objects.all()

    if role == "Client":
        company_id = getattr(user, "company_id", None)
        if company_id is None:
            return Ticket.objects.none()
        return Ticket.objects.filter(company_id=company_id)

    return Ticket.objects.none()
