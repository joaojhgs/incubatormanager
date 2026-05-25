"""Ticket service endpoint tests."""

from __future__ import annotations

import uuid

import pytest
from core.models import Ticket, TicketMessage
from django.urls import reverse
from rest_framework.test import APIClient


def _api_client(role: str, company_id: str | None = None) -> APIClient:
    c = APIClient()
    headers: dict[str, str] = {
        "HTTP_X_USER_ID": str(uuid.uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = company_id
    c.credentials(**headers)
    return c


@pytest.mark.django_db
def test_health_tickets_routes_return_ok() -> None:
    client = APIClient()
    assert client.get("/health/").status_code == 200
    assert client.get("/api/tickets/health/").status_code == 200


@pytest.mark.django_db
def test_staff_can_create_ticket_with_company() -> None:
    staff = _api_client("Staff")
    payload = {
        "company_id": str(uuid.uuid4()),
        "subject": "Power outage",
        "description": "Room 11 lights are off",
    }
    response = staff.post(reverse("ticket-list-create"), payload)
    assert response.status_code == 201
    data = response.json()
    assert data["subject"] == payload["subject"]
    assert data["company_id"] == payload["company_id"]
    assert data["created_by_role"] == "Staff"


@pytest.mark.django_db
def test_staff_lists_all_tickets() -> None:
    for idx in range(2):
        Ticket.objects.create(
            company_id=uuid.uuid4(),
            created_by_id=uuid.uuid4(),
            created_by_role="Staff",
            subject=f"A-{idx}",
            description="desc",
        )

    staff = _api_client("Staff")
    response = staff.get(reverse("ticket-list-create"))
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2

@pytest.mark.django_db
def test_client_can_create_ticket_for_own_company() -> None:
    cid = uuid.uuid4()
    client = _api_client("Client", company_id=str(cid))
    payload = {
        "company_id": str(uuid.uuid4()),
        "subject": "Invoice request",
        "description": "Need copy of invoice",
    }
    response = client.post(reverse("ticket-list-create"), payload)
    assert response.status_code == 201
    assert response.json()["company_id"] == str(cid)


@pytest.mark.django_db
def test_client_can_view_own_tickets_only() -> None:
    own = uuid.uuid4()
    other = uuid.uuid4()
    Ticket.objects.create(
        company_id=own,
        created_by_id=uuid.uuid4(),
        created_by_role="Client",
        subject="Mine",
        description="mine",
    )
    Ticket.objects.create(
        company_id=other,
        created_by_id=uuid.uuid4(),
        created_by_role="Client",
        subject="Other",
        description="other",
    )

    response = _api_client("Client", company_id=str(own)).get(reverse("ticket-list-mine"))
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["subject"] == "Mine"


@pytest.mark.django_db
def test_client_cannot_list_all_tickets() -> None:
    response = _api_client("Client", company_id=str(uuid.uuid4())).get(
        reverse("ticket-list-create")
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_client_can_read_and_post_message_to_own_ticket() -> None:
    cid = uuid.uuid4()
    ticket = Ticket.objects.create(
        company_id=cid,
        created_by_id=uuid.uuid4(),
        created_by_role="Client",
        subject="Issue",
        description="Something wrong",
    )
    client = _api_client("Client", company_id=str(cid))

    response = client.get(reverse("ticket-detail", args=[ticket.pk]))
    assert response.status_code == 200
    assert response.json()["id"] == str(ticket.pk)

    msg_response = client.post(
        reverse("ticket-messages", args=[ticket.pk]),
        {"body": "Can you investigate?"},
    )
    assert msg_response.status_code == 201
    assert msg_response.json()["body"] == "Can you investigate?"
    assert TicketMessage.objects.filter(ticket=ticket).count() == 1


@pytest.mark.django_db
def test_client_cannot_access_foreign_ticket() -> None:
    own = uuid.uuid4()
    other = uuid.uuid4()
    ticket = Ticket.objects.create(
        company_id=other,
        created_by_id=uuid.uuid4(),
        created_by_role="Client",
        subject="Foreign",
        description="not ours",
    )
    response = _api_client("Client", company_id=str(own)).get(
        reverse("ticket-detail", args=[ticket.pk])
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_client_message_denied_on_foreign_ticket() -> None:
    own = uuid.uuid4()
    other = uuid.uuid4()
    ticket = Ticket.objects.create(
        company_id=other,
        created_by_id=uuid.uuid4(),
        created_by_role="Client",
        subject="Foreign",
        description="not ours",
    )
    response = _api_client("Client", company_id=str(own)).post(
        reverse("ticket-messages", args=[ticket.pk]),
        {"body": "Oops"},
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_staff_can_update_ticket_status() -> None:
    ticket = Ticket.objects.create(
        company_id=uuid.uuid4(),
        created_by_id=uuid.uuid4(),
        created_by_role="Client",
        subject="Escalation",
        description="urgent",
    )

    staff = _api_client("Staff")
    response = staff.patch(
        reverse("ticket-detail", args=[ticket.pk]),
        {"status": "Closed"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Closed"


@pytest.mark.django_db
def test_staff_restriction_on_client_role_update() -> None:
    ticket = Ticket.objects.create(
        company_id=uuid.uuid4(),
        created_by_id=uuid.uuid4(),
        created_by_role="Client",
        subject="Escalation",
        description="urgent",
    )
    response = _api_client("Client", company_id=str(ticket.company_id)).patch(
        reverse("ticket-detail", args=[ticket.pk]),
        {"status": "Closed"},
        format="json",
    )
    assert response.status_code == 403
    assert Ticket.objects.get(pk=ticket.pk).status == Ticket.Status.OPEN


@pytest.mark.django_db
def test_unauthenticated_requests_get_401() -> None:
    response = APIClient().get(reverse("ticket-list-create"))
    assert response.status_code == 401
