"""Service helpers for finance query scoping and aggregation."""

from __future__ import annotations

from django.db.models import QuerySet

from core.models import Payment


def payment_scope_for_user(user: object) -> QuerySet[Payment]:
    """Return user-scoped payment queryset."""

    role = getattr(user, "role", None)
    if role in {"Director", "Staff"}:
        return Payment.objects.all()

    if role == "Client":
        company_id = getattr(user, "company_id", None)
        if company_id is None:
            return Payment.objects.none()
        return Payment.objects.filter(company_id=company_id)

    return Payment.objects.none()
