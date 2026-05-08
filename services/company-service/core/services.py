"""Domain operations for company-service."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from core.models import MaturityStage


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
