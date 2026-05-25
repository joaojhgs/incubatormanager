"""Ticket-domain endpoints."""

from __future__ import annotations

import uuid

import pytest
from core.models import Ticket, TicketMessage
from rest_framework.test import APIClient

LIST_URL = "/api/tickets/"
MY_URL = "/api/tickets/my/"


def _api_client(role: str, company_id: str | None = None) -> APIClient:
    client = APIClient()
    headers: dict[str, str] = {
        "HTTP_X_USER_ID": str(uuid.uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = company_id
    client.credentials(**headers)
    return client


def _create_ticket(
    *,
    company_id: str,
    subject: str = "Default subject",
    description: str = "Default description",
    status: str = Ticket.Status.OPEN,
    assigned_to: uuid.UUID | None = None,
) -> Ticket:
    return Ticket.objects.create(
        company_id=company_id,
        subject=subject,
        description=description,
        status=status,
        assigned_to=assigned_to,
        created_by_user_id=uuid.uuid4(),
        created_by_role="Client",
    )


@pytest.mark.django_db
def test_ticket_unauthenticated_is_denied() -> None:
    response = APIClient().get(LIST_URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_ticket_list_staff_and_client_scopes() -> None:
    c1 = str(uuid.uuid4())
    c2 = str(uuid.uuid4())
    mine = _create_ticket(company_id=c1, subject="Mine")
    _ = _create_ticket(company_id=c2, subject="Theirs")

    staff_client = _api_client("Staff")
    staff_resp = staff_client.get(LIST_URL)
    assert staff_resp.status_code == 200
    staff_ids = {row["id"] for row in staff_resp.json()}
    assert str(mine.pk) in staff_ids

    client = _api_client("Client", company_id=c1)
    client_resp = client.get(LIST_URL)
    assert client_resp.status_code == 200
    client_payload = client_resp.json()
    client_ids = {row["id"] for row in client_payload}
    assert str(mine.pk) in client_ids
    assert all(row["company_id"] == c1 for row in client_payload)


@pytest.mark.django_db
def test_ticket_list_staff_filters_by_status_company_and_assignee() -> None:
    company_id = str(uuid.uuid4())
    other_company_id = str(uuid.uuid4())
    assignee = uuid.uuid4()
    matching = _create_ticket(
        company_id=company_id,
        subject="Assigned",
        status=Ticket.Status.IN_PROGRESS,
        assigned_to=assignee,
    )
    _create_ticket(company_id=company_id, status=Ticket.Status.OPEN, assigned_to=assignee)
    _create_ticket(
        company_id=other_company_id,
        status=Ticket.Status.IN_PROGRESS,
        assigned_to=assignee,
    )
    _create_ticket(
        company_id=company_id,
        status=Ticket.Status.IN_PROGRESS,
        assigned_to=uuid.uuid4(),
    )

    response = _api_client("Staff").get(
        LIST_URL,
        {
            "company_id": company_id,
            "status": Ticket.Status.IN_PROGRESS,
            "assigned_to": str(assignee),
        },
    )

    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [str(matching.pk)]


@pytest.mark.django_db
def test_ticket_list_staff_can_filter_unassigned() -> None:
    company_id = str(uuid.uuid4())
    unassigned = _create_ticket(company_id=company_id, subject="Unassigned")
    _create_ticket(company_id=company_id, assigned_to=uuid.uuid4())

    response = _api_client("Staff").get(LIST_URL, {"assigned_to": "unassigned"})

    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [str(unassigned.pk)]


@pytest.mark.django_db
def test_ticket_detail_scope_is_enforced() -> None:
    mine = _create_ticket(company_id=str(uuid.uuid4()), subject="Own")
    other = _create_ticket(company_id=str(uuid.uuid4()), subject="Other")

    client = _api_client("Client", company_id=str(mine.company_id))
    own = client.get(f"/api/tickets/{mine.pk}/")
    assert own.status_code == 200

    forbidden = client.get(f"/api/tickets/{other.pk}/")
    assert forbidden.status_code == 404


@pytest.mark.django_db
def test_ticket_create_client_defaults_to_own_company_and_staff_can_create_for_any() -> None:
    company_id = str(uuid.uuid4())
    client = _api_client("Client", company_id=company_id)
    payload = {"subject": "New issue", "description": "Needs help"}
    response = client.post(LIST_URL, data=payload, format="json")
    assert response.status_code == 201
    data = response.data
    assert data["company_id"] == company_id
    assert data["subject"] == "New issue"
    assert data["status"] == Ticket.Status.OPEN

    staff = _api_client("Staff")
    response_staff = staff.post(
        LIST_URL,
        data={"company_id": company_id, "subject": "Staff issue", "description": "..."},
        format="json",
    )
    assert response_staff.status_code == 201
    staff_data = response_staff.data
    assert staff_data["company_id"] == company_id

    response_bad_staff = staff.post(
        LIST_URL,
        data={"subject": "No company", "description": "bad"},
        format="json",
    )
    assert response_bad_staff.status_code == 400


@pytest.mark.django_db
def test_ticket_my_returns_client_only_tickets() -> None:
    cid = str(uuid.uuid4())
    other = str(uuid.uuid4())
    mine1 = _create_ticket(company_id=cid, subject="A")
    _ = _create_ticket(company_id=other, subject="B")

    response = _api_client("Client", company_id=cid).get(MY_URL)
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()}
    assert ids == {str(mine1.pk)}


@pytest.mark.django_db
def test_ticket_messages_are_client_or_staff_scoped() -> None:
    company_id = str(uuid.uuid4())
    foreign = str(uuid.uuid4())
    ticket = _create_ticket(company_id=company_id, subject="Need")
    foreign_ticket = _create_ticket(company_id=foreign, subject="Other")

    client = _api_client("Client", company_id=company_id)
    post_resp = client.post(
        f"/api/tickets/{ticket.pk}/messages/",
        data={"content": "Hi"},
        format="json",
    )
    assert post_resp.status_code == 201
    assert post_resp.json()["content"] == "Hi"
    assert TicketMessage.objects.filter(ticket=ticket).count() == 1

    blocked = client.get(f"/api/tickets/{ticket.pk}/messages/")
    assert blocked.status_code == 405

    forbidden = _api_client("Client", company_id=company_id).post(
        f"/api/tickets/{foreign_ticket.pk}/messages/",
        data={"content": "Nope"},
        format="json",
    )
    assert forbidden.status_code == 404


@pytest.mark.django_db
def test_ticket_detail_includes_ordered_thread_messages() -> None:
    company_id = str(uuid.uuid4())
    ticket = _create_ticket(company_id=company_id, subject="Thread")
    first = TicketMessage.objects.create(
        ticket=ticket,
        author_user_id=uuid.uuid4(),
        author_role="Client",
        content="Initial question",
    )
    second = TicketMessage.objects.create(
        ticket=ticket,
        author_user_id=uuid.uuid4(),
        author_role="Staff",
        content="Staff reply",
    )

    response = _api_client("Client", company_id=company_id).get(f"/api/tickets/{ticket.pk}/")

    assert response.status_code == 200
    messages = response.json()["messages"]
    assert [row["id"] for row in messages] == [str(first.pk), str(second.pk)]
    assert [row["content"] for row in messages] == ["Initial question", "Staff reply"]


@pytest.mark.django_db
def test_ticket_update_staff_only_and_client_forbidden() -> None:
    c = str(uuid.uuid4())
    ticket = _create_ticket(company_id=c)

    staff = _api_client("Staff")
    staff_update = staff.patch(
        f"/api/tickets/{ticket.pk}/",
        data={"status": Ticket.Status.IN_PROGRESS, "assigned_to": str(uuid.uuid4())},
        format="json",
    )
    assert staff_update.status_code == 200
    assert staff_update.json()["status"] == Ticket.Status.IN_PROGRESS
    assert staff_update.json()["assigned_to"] is not None

    client = _api_client("Client", company_id=c)
    client_update = client.patch(
        f"/api/tickets/{ticket.pk}/",
        data={"status": Ticket.Status.CLOSED},
        format="json",
    )
    assert client_update.status_code == 403
