"""Event publish helpers for the contract service."""

from __future__ import annotations

from typing import Any

from django.db import transaction
from ilb_common import event_bus

from core.models import Contract


def _rabbit_url() -> str | None:
    from django.conf import settings

    return str(getattr(settings, "RABBITMQ_URL", "")) or None


def _publish(event_type: str, payload: dict[str, Any]) -> None:
    rabbit_url = _rabbit_url()
    if not rabbit_url:
        return

    transaction.on_commit(lambda: event_bus.publish(rabbit_url, event_type, payload))


def _contract_payload(contract: Contract) -> dict[str, str | int | float | None]:
    return {
        "contract_id": str(contract.id),
        "company_id": str(contract.company_id),
        "space_id": str(contract.space_id),
        "area_sqm": float(contract.area_sqm),
        "rate_per_sqm": float(contract.rate_per_sqm),
        "monthly_fee": float(contract.monthly_fee),
        "start_date": contract.start_date.isoformat(),
        "end_date": contract.end_date.isoformat(),
    }


def publish_contract_activated(contract: Contract) -> None:
    _publish("contract.activated", _contract_payload(contract))


def publish_contract_terminated(contract: Contract) -> None:
    payload = _contract_payload(contract)
    payload["reason"] = contract.termination_reason
    _publish("contract.terminated", payload)


def publish_contract_expired(contract: Contract) -> None:
    payload = {
        "contract_id": str(contract.id),
        "company_id": str(contract.company_id),
        "space_id": str(contract.space_id),
    }
    _publish("contract.expired", payload)
