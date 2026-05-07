"""RBAC and happy-path tests for GET/POST /api/companies/cae/."""

from __future__ import annotations

import uuid

import pytest
from core.models import CAE
from rest_framework.test import APIClient


def _client(role: str, company_id: str | None = None) -> APIClient:
    c = APIClient()
    headers = {
        "HTTP_X_USER_ID": str(uuid.uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = company_id
    c.credentials(**headers)
    return c


URL = "/api/companies/cae/"


# ---------------------------------------------------------------------------
# GET — list
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_cae_list_director() -> None:
    response = _client("Director").get(URL)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_get_cae_list_staff() -> None:
    response = _client("Staff").get(URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_get_cae_list_client() -> None:
    response = _client("Client", company_id=str(uuid.uuid4())).get(URL)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_get_cae_list_unauthenticated() -> None:
    response = APIClient().get(URL)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST — create (Director only)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_post_cae_director_creates_entry() -> None:
    payload = {"code": "9999", "description": "Test sector"}
    response = _client("Director").post(URL, data=payload, format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "9999"
    assert data["description"] == "Test sector"
    assert "id" in data
    assert CAE.objects.filter(code="9999").exists()


@pytest.mark.django_db
def test_post_cae_staff_forbidden() -> None:
    response = _client("Staff").post(URL, data={"code": "1111", "description": "x"}, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_post_cae_client_forbidden() -> None:
    response = _client("Client", company_id=str(uuid.uuid4())).post(
        URL, data={"code": "2222", "description": "x"}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_post_cae_unauthenticated() -> None:
    response = APIClient().post(URL, data={"code": "3333", "description": "x"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_post_cae_duplicate_code_returns_400() -> None:
    CAE.objects.create(id=uuid.uuid4(), code="4444", description="existing")
    response = _client("Director").post(
        URL, data={"code": "4444", "description": "dup"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_get_cae_list_returns_seeded_codes() -> None:
    response = _client("Staff").get(URL)
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert "6201" in codes
