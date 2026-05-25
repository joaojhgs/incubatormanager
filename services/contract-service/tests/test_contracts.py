"""Tests for contract CRUD and lifecycle event behavior."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from core.models import Contract
from django.core.management import call_command
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db(transaction=True)


def _api_client(role: str, company_id: str | None = None) -> APIClient:
    client = APIClient()
    headers = {
        "HTTP_X_USER_ID": str(uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = company_id
    client.credentials(**headers)
    return client


def _contract_payload(**overrides: object) -> dict[str, object]:
    payload = {
        "company_id": str(uuid4()),
        "space_id": str(uuid4()),
        "area_sqm": "50.00",
        "rate_per_sqm": "12.00",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=90)),
    }
    payload.update(overrides)
    return payload


def _make_contract(company_id: str, **overrides: object) -> Contract:
    base_payload = _contract_payload(company_id=company_id)
    area = Decimal(str(base_payload["area_sqm"]))
    rate = Decimal(str(base_payload["rate_per_sqm"]))
    defaults = {
        "company_id": company_id,
        "space_id": str(uuid4()),
        "area_sqm": area,
        "rate_per_sqm": rate,
        "monthly_fee": area * rate,
        "start_date": date.today(),
        "end_date": date.today() + timedelta(days=120),
    }
    defaults.update(overrides)
    return Contract.objects.create(**defaults)


def test_contract_list_detail_company_scope_and_client_isolation() -> None:
    company_a = str(uuid4())
    company_b = str(uuid4())
    _make_contract(company_id=company_a)
    _make_contract(company_id=company_b)

    staff_response = _api_client("Staff").get("/api/contracts/")
    assert staff_response.status_code == 200
    assert len(staff_response.json()) == 2

    own_list = _api_client("Client", company_a).get("/api/contracts/")
    assert own_list.status_code == 200
    assert len(own_list.json()) == 1

    foreign_list = _api_client("Client", company_a).get(
        f"/api/contracts/company/{company_b}/"
    )
    assert foreign_list.status_code == 403

    own_list_by_company = _api_client("Client", company_a).get(
        f"/api/contracts/company/{company_a}/"
    )
    assert own_list_by_company.status_code == 200
    assert len(own_list_by_company.json()) == 1


def test_staff_can_create_contract_with_snapshoted_monthly_fee() -> None:
    payload = _contract_payload()
    response = _api_client("Staff").post("/api/contracts/", data=payload, format="json")
    assert response.status_code == 201

    payload_json = response.json()
    assert Decimal(payload_json["monthly_fee"]) == Decimal("600.00")
    assert payload_json["status"] == Contract.Status.DRAFT


def test_client_cannot_create_contract() -> None:
    payload = _contract_payload()
    response = _api_client("Client", company_id=payload["company_id"]).post(
        "/api/contracts/",
        data=payload,
        format="json",
    )
    assert response.status_code == 403


def test_activate_contract_emits_contract_activated_event_on_commit() -> None:
    payload = _contract_payload()
    created = _api_client("Staff").post("/api/contracts/", data=payload, format="json")
    assert created.status_code == 201
    contract_id = created.json()["id"]

    with patch("core.events._rabbit_url", return_value="amqp://rabbit"), patch(
        "core.events.transaction.on_commit") as on_commit, patch(
        "core.events.event_bus.publish"
    ) as publish:
        response = _api_client("Staff").patch(
            f"/api/contracts/{contract_id}/activate/",
            data={},
            format="json",
        )
        assert response.status_code == 200
        assert Contract.objects.get(id=contract_id).status == Contract.Status.ACTIVE
        assert on_commit.call_count == 1

        on_commit.call_args.args[0]()
        assert publish.call_count == 1
        called = publish.call_args.args
        assert called[1] == "contract.activated"
        payload = called[2]
        assert payload["contract_id"] == contract_id
        assert payload["monthly_fee"] == 600.0


def test_terminate_contract_emits_contract_terminated_event_and_freezes_reason() -> None:
    payload = _contract_payload()
    created = _api_client("Staff").post("/api/contracts/", data=payload, format="json")
    assert created.status_code == 201
    contract_id = created.json()["id"]

    response = _api_client("Staff").patch(
        f"/api/contracts/{contract_id}/activate/",
        data={},
        format="json",
    )
    assert response.status_code == 200

    with patch("core.events._rabbit_url", return_value="amqp://rabbit"), patch(
        "core.events.transaction.on_commit"
    ) as on_commit, patch(
        "core.events.event_bus.publish"
    ) as publish:
        response = _api_client("Staff").patch(
            f"/api/contracts/{contract_id}/terminate/",
            data={"reason": "breach"},
            format="json",
        )
        assert response.status_code == 200
        assert Contract.objects.get(id=contract_id).status == Contract.Status.TERMINATED

        on_commit.call_args.args[0]()
        called = publish.call_args.args
        assert called[1] == "contract.terminated"
        assert called[2]["reason"] == "breach"


def test_expire_contracts_command_is_idempotent() -> None:
    old_date = date.today() - timedelta(days=30)
    active_to_expire = _make_contract(
        company_id=str(uuid4()),
        start_date=old_date - timedelta(days=30),
        end_date=old_date,
        status=Contract.Status.ACTIVE,
    )
    _make_contract(
        company_id=str(uuid4()),
        start_date=date.today(),
        end_date=date.today() + timedelta(days=5),
        status=Contract.Status.ACTIVE,
    )

    with patch(
        "core.management.commands.expire_contracts.publish_contract_expired"
    ) as publish, patch(
        "core.events.transaction.on_commit",
        side_effect=lambda callback: callback(),
    ):
        call_command("expire_contracts")
        active_to_expire.refresh_from_db()
        assert active_to_expire.status == Contract.Status.EXPIRED
        assert publish.call_count == 1

        call_command("expire_contracts")
        assert publish.call_count == 1
