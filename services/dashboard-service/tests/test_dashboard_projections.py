"""Tests for dashboard materialized projections and analytics endpoints."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import patch

import pytest
from core.handlers import handle_event
from core.models import (
    BookingProjection,
    CompanyProjection,
    ContractProjection,
    DashboardSnapshot,
    EmployeeProjection,
    PaymentProjection,
    ProcessedEvent,
)
from django.core.management import call_command
from rest_framework.test import APIClient


def _client(role: str = "Staff") -> APIClient:
    client = APIClient()
    client.credentials(HTTP_X_USER_ID=str(uuid.uuid4()), HTTP_X_USER_ROLE=role)
    return client


def _event(event_type: str, payload: dict[str, object], event_id: str | None = None):
    return {
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": event_type,
        "occurred_at": "2026-05-25T00:00:00Z",
        "payload": payload,
    }


class _FakeHTTPResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.mark.django_db
def test_dashboard_event_handlers_materialize_aggregates_idempotently() -> None:
    company_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    contract_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    space_id = uuid.uuid4()

    company_event = _event(
        "company.created",
        {
            "company_id": str(company_id),
            "name": "Acme",
            "cae_code": "62010",
            "maturity_stage_name": "Scale",
        },
        event_id="evt-company",
    )
    handle_event(company_event)
    handle_event(company_event)
    handle_event(
        _event(
            "employee.changed",
            {
                "company_id": str(company_id),
                "employee_id": str(employee_id),
                "action": "created",
                "employee_type": "Founder",
            },
        )
    )
    handle_event(
        _event(
            "contract.activated",
            {
                "contract_id": str(contract_id),
                "company_id": str(company_id),
                "space_id": str(space_id),
                "area_sqm": "50.5",
                "rate_per_sqm": "10",
                "monthly_fee": "505",
                "start_date": "2026-05-01",
                "end_date": "2027-05-01",
            },
        )
    )
    handle_event(
        _event(
            "booking.approved",
            {
                "booking_id": str(booking_id),
                "company_id": str(company_id),
                "space_id": str(space_id),
                "start_time": "2026-05-25T10:00:00Z",
                "end_time": "2026-05-25T12:00:00Z",
                "quoted_price": "25.75",
            },
        )
    )
    handle_event(
        _event(
            "payment.recorded",
            {
                "payment_id": str(payment_id),
                "company_id": str(company_id),
                "contract_id": str(contract_id),
                "amount": "505.00",
                "paid_at": "2026-05-25T14:00:00Z",
            },
        )
    )

    assert ProcessedEvent.objects.filter(event_id="evt-company").count() == 1
    assert CompanyProjection.objects.get(company_id=company_id).cae_code == "62010"
    assert EmployeeProjection.objects.get(employee_id=employee_id).is_active is True
    assert ContractProjection.objects.get(contract_id=contract_id).is_active is True
    assert BookingProjection.objects.get(booking_id=booking_id).status == "approved"
    assert PaymentProjection.objects.get(payment_id=payment_id).amount == pytest.approx(505)


@pytest.mark.django_db
@patch("core.views.urlopen")
def test_dashboard_analytics_endpoints_read_materialized_rows(urlopen) -> None:
    urlopen.return_value = _FakeHTTPResponse(json.dumps({"status": "ok"}).encode())
    company_id = uuid.uuid4()
    space_id = uuid.uuid4()
    CompanyProjection.objects.create(
        company_id=company_id,
        name="Acme",
        cae_code="62010",
        maturity_stage_name="Scale",
    )
    EmployeeProjection.objects.create(
        employee_id=uuid.uuid4(),
        company_id=company_id,
        employee_type="Founder",
    )
    ContractProjection.objects.create(
        contract_id=uuid.uuid4(),
        company_id=company_id,
        space_id=space_id,
        monthly_fee="500.00",
        is_active=True,
    )
    BookingProjection.objects.create(
        booking_id=uuid.uuid4(),
        company_id=company_id,
        space_id=space_id,
        status="approved",
        quoted_price="20.00",
    )
    PaymentProjection.objects.create(
        payment_id=uuid.uuid4(),
        company_id=company_id,
        amount="500.00",
        paid_at=datetime(2026, 5, 25, 12, 0, tzinfo=UTC),
    )
    DashboardSnapshot.objects.create(source="finance", payload={"overdue": 2})

    client = _client()
    companies = client.get("/api/dashboard/companies/")
    spaces = client.get("/api/dashboard/spaces/")
    finance = client.get("/api/dashboard/finance/")
    overview = client.get("/api/dashboard/overview/")

    assert companies.status_code == 200
    assert companies.json()["by_sector"] == [{"cae_code": "62010", "total": 1}]
    assert spaces.status_code == 200
    assert spaces.json()["occupancy_percent"] == 100.0
    assert finance.status_code == 200
    assert finance.json()["overdue_count"] == 2
    assert overview.status_code == 200
    assert overview.json()["kpis"]["companies"] == 1
    assert overview.json()["kpis"]["pending_bookings"] == 1


@pytest.mark.django_db
@patch("core.views.urlopen")
def test_dashboard_rebuild_command_stores_metric_snapshots(urlopen) -> None:
    payload = json.dumps({"total": 3, "overdue": 1}).encode()
    urlopen.side_effect = [_FakeHTTPResponse(payload), _FakeHTTPResponse(payload)]

    call_command("dashboard_rebuild", source=["company", "finance"])

    assert DashboardSnapshot.objects.get(source="company").payload == {"total": 3, "overdue": 1}
    assert DashboardSnapshot.objects.get(source="finance").payload == {"total": 3, "overdue": 1}
    assert urlopen.call_count == 2
