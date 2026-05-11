"""Domain operations for company-service."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import Prefetch, QuerySet

from core.models import Company, Employee, MaturityStage


def create_maturity_stage(
    *,
    name: str,
    rate_per_sqm: Decimal,
    description: str = "",
    display_order: int = 0,
) -> MaturityStage:
    return MaturityStage.objects.create(
        name=name,
        rate_per_sqm=rate_per_sqm,
        description=description,
        display_order=display_order,
    )


def update_maturity_stage(instance: MaturityStage, **updates: Any) -> MaturityStage:
    allowed = frozenset({"name", "rate_per_sqm", "description", "display_order"})
    for key, value in updates.items():
        if key not in allowed or value is None:
            continue
        setattr(instance, key, value)
    instance.save()
    return instance


def company_list_queryset(role: str, company_id: str | None) -> QuerySet[Company]:
    """Base queryset for listing companies — scoped by RBAC."""

    qs = Company.objects.select_related("cae", "maturity_stage").order_by("name")
    if role in {"Director", "Staff"}:
        return qs
    if role == "Client":
        if company_id is None:
            return qs.none()
        return qs.filter(pk=company_id, is_active=True)
    return qs.none()


def company_detail_queryset(role: str, company_id: str | None) -> QuerySet[Company]:
    """Detail queryset — active companies only; FKs joined; employees prefetched."""

    emp_qs = Employee.active.order_by("name")
    qs = Company.active.select_related("cae", "maturity_stage").prefetch_related(
        Prefetch("employees", queryset=emp_qs)
    )
    if role in {"Director", "Staff"}:
        return qs
    if role == "Client":
        if company_id is None:
            return qs.none()
        return qs.filter(pk=company_id)
    return qs.none()
