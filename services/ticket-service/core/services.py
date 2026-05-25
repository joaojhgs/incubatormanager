"""Reusable ticket-scoped queryset helpers."""

from __future__ import annotations

from django.db import models

from core.models import Ticket


def ticket_scope_for_user(user: object) -> models.QuerySet[Ticket]:
    """Return tickets visible to a user.

    Staff and directors can read all tickets. Client users are restricted to
    their ``company_id``. Unknown roles return no rows.
    """

    role = getattr(user, "role", None)
    if role in {"Staff", "Director"}:
        return Ticket.objects.all()

    if role == "Client":
        company_id = getattr(user, "company_id", None)
        if company_id is None:
            return Ticket.objects.none()
        return Ticket.objects.filter(company_id=company_id)

    return Ticket.objects.none()
