"""Tests for ``manage.py seed_dev_users``."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from users.models import User


@pytest.mark.django_db
def test_seed_dev_users_requires_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTH_DEV_SEED_PASSWORD", raising=False)
    with pytest.raises(CommandError, match="AUTH_DEV_SEED_PASSWORD"):
        call_command("seed_dev_users")


@pytest.mark.django_db
def test_seed_dev_users_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_DEV_SEED_PASSWORD", "shared-secret-seed")
    call_command("seed_dev_users")
    assert User.objects.count() == 10
    assert User.objects.filter(role=User.Role.DIRECTOR).count() == 1
    assert User.objects.filter(role=User.Role.STAFF).count() == 3
    assert User.objects.filter(role=User.Role.CLIENT).count() == 6

    call_command("seed_dev_users")
    assert User.objects.count() == 10


@pytest.mark.django_db
def test_seed_dev_users_refreshes_existing_passwords(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_DEV_SEED_PASSWORD", "first-shared-secret")
    call_command("seed_dev_users")
    director = User.objects.get(email="dev.director@ilb.test")
    assert director.check_password("first-shared-secret")

    monkeypatch.setenv("AUTH_DEV_SEED_PASSWORD", "second-shared-secret")
    call_command("seed_dev_users")

    director.refresh_from_db()
    assert director.check_password("second-shared-secret")
    assert not director.check_password("first-shared-secret")


@pytest.mark.django_db
def test_seed_dev_users_role_password_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_DEV_SEED_PASSWORD", "fallback")
    monkeypatch.setenv("AUTH_DEV_SEED_DIRECTOR_PASSWORD", "dir-only")
    monkeypatch.setenv("AUTH_DEV_SEED_STAFF_PASSWORD", "staff-only")
    monkeypatch.setenv("AUTH_DEV_SEED_CLIENT_PASSWORD", "client-only")
    call_command("seed_dev_users")

    director = User.objects.get(email="dev.director@ilb.test")
    assert director.check_password("dir-only")

    staff = User.objects.get(email="dev.staff1@ilb.test")
    assert staff.check_password("staff-only")

    client = User.objects.get(email="dev.client.1a@ilb.test")
    assert client.check_password("client-only")


@pytest.mark.django_db
def test_seed_dev_users_clients_have_distinct_companies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_DEV_SEED_PASSWORD", "x")
    call_command("seed_dev_users")
    company_ids = set(
        User.objects.filter(role=User.Role.CLIENT).values_list("company_id", flat=True)
    )
    assert len(company_ids) == 3
