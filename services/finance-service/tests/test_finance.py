"""Finance-service API and domain behavior tests."""

from __future__ import annotations

import datetime as dt
import uuid
from datetime import UTC
from unittest.mock import patch

import pytest
from core.handlers import (
    handle_booking_approved,
    handle_contract_activated,
    handle_contract_inactive,
)
from core.management.commands.generate_monthly_billing import _month_end, _month_start
from core.management.commands.generate_monthly_billing import _to_date as cmd_to_date
from core.models import BillingContract, Payment
from django.core.management import call_command
from rest_framework.test import APIClient


def _api_client(role: str, company_id: str | None = None) -> APIClient:
    c = APIClient()
    headers = {
        "HTTP_X_USER_ID": str(uuid.uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = company_id
    c.credentials(**headers)
    return c


def _create_payment(
    *,
    company_id: str,
    source: str = Payment.Source.CONTRACT,
    **overrides: object,
) -> Payment:
    payload = {
        "company_id": uuid.UUID(company_id),
        "source": source,
        "contract_id": overrides.pop("contract_id", uuid.uuid4()),
        "amount": overrides.pop("amount", "120.00"),
        "status": overrides.pop("status", Payment.Status.PENDING),
    }
    payload.update(overrides)
    return Payment.objects.create(**payload)


def _event(
    payload: dict[str, object],
    *,
    event_type: str,
    event_id: str | None = None,
) -> dict[str, object]:
    return {
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": event_type,
        "occurred_at": dt.datetime.now(UTC).isoformat(),
        "payload": payload,
    }


@pytest.mark.django_db
def test_finance_unauthenticated_is_denied() -> None:
    response = APIClient().get("/api/finance/payments/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_finance_list_scope_is_role_aware() -> None:
    c1 = str(uuid.uuid4())
    c2 = str(uuid.uuid4())
    payment1 = _create_payment(company_id=c1, amount="110.00")
    payment2 = _create_payment(company_id=c2, amount="220.00")

    staff_resp = _api_client("Staff").get("/api/finance/payments/")
    assert staff_resp.status_code == 200
    staff_ids = {row["id"] for row in staff_resp.json()}
    assert staff_ids == {str(payment1.id), str(payment2.id)}

    client_resp = _api_client("Client", company_id=c1).get("/api/finance/payments/")
    assert client_resp.status_code == 200
    payload = client_resp.json()
    assert {row["id"] for row in payload} == {str(payment1.id)}
    assert all(row["company_id"] == c1 for row in payload)


@pytest.mark.django_db
def test_payment_detail_patch_marks_paid_and_publishes_event() -> None:
    company_id = str(uuid.uuid4())
    payment = _create_payment(company_id=company_id, source=Payment.Source.BOOKING)

    with (
        patch("core.views.transaction.on_commit") as on_commit,
        patch("core.handlers.event_bus.publish") as publish,
    ):
        # Ensure env-gated event publishing path executes.
        import os

        os.environ["RABBITMQ_URL"] = "amqp://rabbit"
        response = _api_client("Staff", company_id=company_id).patch(
            f"/api/finance/payments/{payment.id}/",
            data={"status": Payment.Status.PAID},
            format="json",
        )
        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PAID
        assert on_commit.call_count == 1

        callback = on_commit.call_args.args[0]
        callback()
        publish.assert_called_once()
        assert publish.call_args.args[1] == "payment.recorded"
        payload = publish.call_args.args[2]
        assert payload["payment_id"] == str(payment.id)
        assert payload["company_id"] == company_id


@pytest.mark.django_db
def test_payment_detail_patch_client_is_forbidden() -> None:
    company_id = str(uuid.uuid4())
    payment = _create_payment(company_id=company_id, source=Payment.Source.BOOKING)

    response = _api_client("Client", company_id=company_id).patch(
        f"/api/finance/payments/{payment.id}/",
        data={"status": Payment.Status.PAID},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_company_payments_endpoint_is_client_scoped() -> None:
    mine = str(uuid.uuid4())
    other = str(uuid.uuid4())
    payment = _create_payment(company_id=mine, amount="90.00")
    _create_payment(company_id=other, amount="10.00")

    client_resp = _api_client("Client", company_id=mine).get(
        f"/api/finance/payments/company/{mine}/"
    )
    assert client_resp.status_code == 200
    assert {row["id"] for row in client_resp.json()} == {str(payment.id)}

    forbidden = _api_client("Client", company_id=mine).get(
        f"/api/finance/payments/company/{other}/"
    )
    assert forbidden.status_code == 404


@pytest.mark.django_db
def test_contract_and_booking_handlers_are_idempotent() -> None:
    company_id = str(uuid.uuid4())
    contract_id = str(uuid.uuid4())
    space_id = str(uuid.uuid4())
    booking_id = str(uuid.uuid4())

    contract_payload = {
        "contract_id": contract_id,
        "company_id": company_id,
        "space_id": space_id,
        "area_sqm": "10",
        "rate_per_sqm": "8",
        "monthly_fee": "80",
        "start_date": "2026-05-01",
        "end_date": "2026-12-31",
    }
    contract_event_id = str(uuid.uuid4())
    handle_contract_activated(
        _event(
            contract_payload,
            event_type="contract.activated",
            event_id=contract_event_id,
        )
    )
    handle_contract_activated(
        _event(
            contract_payload,
            event_type="contract.activated",
            event_id=contract_event_id,
        )
    )
    assert BillingContract.objects.count() == 1

    booking_payload = {
        "booking_id": booking_id,
        "company_id": company_id,
        "space_id": space_id,
        "start_time": "2026-06-01T10:00:00+00:00",
        "quoted_price": "300",
        "equipment_ids": [],
    }
    booking_event_id = str(uuid.uuid4())
    handle_booking_approved(
        _event(
            booking_payload,
            event_type="booking.approved",
            event_id=booking_event_id,
        )
    )
    handle_booking_approved(
        _event(
            booking_payload,
            event_type="booking.approved",
            event_id=booking_event_id,
        )
    )
    assert Payment.objects.filter(source=Payment.Source.BOOKING).count() == 1


@pytest.mark.django_db
def test_contract_end_events_deactivate_billing_contract_idempotently() -> None:
    contract_id = uuid.uuid4()
    BillingContract.objects.create(
        contract_id=contract_id,
        company_id=uuid.uuid4(),
        space_id=uuid.uuid4(),
        area_sqm="10.00",
        rate_per_sqm="8.00",
        monthly_fee="80.00",
        start_date=dt.date(2026, 1, 1),
        is_active=True,
    )

    event_id = str(uuid.uuid4())
    event = _event(
        {"contract_id": str(contract_id), "company_id": str(uuid.uuid4())},
        event_type="contract.terminated",
        event_id=event_id,
    )
    handle_contract_inactive(event)
    handle_contract_inactive(event)

    contract = BillingContract.objects.get(contract_id=contract_id)
    assert contract.is_active is False
    assert Payment.objects.count() == 0


@pytest.mark.django_db
def test_generate_monthly_billing_is_idempotent() -> None:
    BillingContract.objects.create(
        contract_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        space_id=uuid.uuid4(),
        area_sqm="12.5",
        rate_per_sqm="8.00",
        monthly_fee="100.00",
        start_date=dt.date(2026, 1, 1),
        is_active=True,
    )

    call_command("generate_monthly_billing", as_of="2026-06-17")
    assert Payment.objects.filter(source=Payment.Source.CONTRACT).count() == 1

    call_command("generate_monthly_billing", as_of="2026-06-20")
    assert Payment.objects.filter(source=Payment.Source.CONTRACT).count() == 1


@pytest.mark.django_db
def test_mark_overdue_payments_is_idempotent() -> None:
    _create_payment(
        company_id=str(uuid.uuid4()),
        amount="50.00",
        status=Payment.Status.PENDING,
        due_date=dt.date(2026, 5, 1),
    )
    _create_payment(
        company_id=str(uuid.uuid4()),
        amount="70.00",
        status=Payment.Status.OVERDUE,
        due_date=dt.date(2026, 4, 1),
    )

    call_command("mark_overdue_payments", as_of="2026-05-02")
    assert Payment.objects.filter(status=Payment.Status.OVERDUE).count() == 2

    call_command("mark_overdue_payments", as_of="2026-05-02")
    assert Payment.objects.filter(status=Payment.Status.OVERDUE).count() == 2


@pytest.mark.django_db
def test_dashboard_and_reports_are_scoped() -> None:
    cid1 = uuid.uuid4()
    _create_payment(
        company_id=str(cid1),
        source=Payment.Source.CONTRACT,
        amount="100",
        status=Payment.Status.PAID,
    )
    _create_payment(
        company_id=str(cid1),
        source=Payment.Source.CONTRACT,
        amount="50",
        status=Payment.Status.PENDING,
    )
    _create_payment(
        company_id=str(cid1),
        source=Payment.Source.BOOKING,
        amount="25",
        status=Payment.Status.OVERDUE,
    )
    other = uuid.uuid4()
    _create_payment(
        company_id=str(other),
        source=Payment.Source.BOOKING,
        amount="12",
        status=Payment.Status.PENDING,
    )

    staff_resp = _api_client("Staff").get("/api/finance/dashboard/")
    assert staff_resp.status_code == 200
    assert staff_resp.json()["total_payments"] == 4

    client_resp = _api_client("Client", company_id=str(cid1)).get("/api/finance/dashboard/")
    assert client_resp.status_code == 200
    assert client_resp.json()["total_payments"] == 3

    reports = _api_client("Staff").get("/api/finance/reports/")
    assert reports.status_code == 200
    assert len(reports.json()) == 2


@pytest.mark.django_db
def test_consumer_command_wires_expected_routing_keys() -> None:
    with patch("core.management.commands.consume_finance_events.event_bus.subscribe") as subscribe:
        call_command(
            "consume_finance_events",
            rabbitmq_url="amqp://rabbit",
            queue="finance.unit-test",
        )
        assert subscribe.call_count == 1
        call_kwargs = subscribe.call_args.kwargs
        assert call_kwargs["queue"] == "finance.unit-test"
        call_args = subscribe.call_args.args
        assert set(call_args[1]) == {
            "contract.activated",
            "contract.expired",
            "contract.terminated",
            "booking.approved",
        }


@pytest.mark.django_db
def test_generate_monthly_billing_rejects_invalid_as_of() -> None:
    with pytest.raises(ValueError, match="invalid --as-of date"):
        cmd_to_date("2026-99-99")


def test_month_range_helpers_are_consistent() -> None:
    anchor = dt.date(2026, 2, 15)
    assert _month_start(anchor) == dt.date(2026, 2, 1)
    assert _month_end(anchor) == dt.date(2026, 2, 28)
