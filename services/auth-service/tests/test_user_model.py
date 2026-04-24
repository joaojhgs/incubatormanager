"""Tests for the custom User model."""

from __future__ import annotations

import uuid

import pytest
from django.db import IntegrityError
from users.models import User


@pytest.mark.django_db
def test_create_user_persists_uuid_pk_and_hashed_password() -> None:
    user = User.objects.create_user(
        "client@example.com",
        "secret-pass",
        role=User.Role.CLIENT,
        first_name="Casey",
        last_name="Client",
        company_id=uuid.uuid4(),
    )
    assert isinstance(user.pk, uuid.UUID)
    assert user.check_password("secret-pass")
    assert not user.check_password("wrong")


@pytest.mark.django_db
def test_email_must_be_unique() -> None:
    User.objects.create_user(
        "dup@example.com",
        "x",
        role=User.Role.STAFF,
        first_name="Sam",
        last_name="Staff",
    )
    with pytest.raises(IntegrityError):
        User.objects.create_user(
            "dup@example.com",
            "y",
            role=User.Role.STAFF,
            first_name="Sara",
            last_name="Staff",
        )


@pytest.mark.django_db
def test_company_id_optional_for_staff() -> None:
    user = User.objects.create_user(
        "staff@example.com",
        "x",
        role=User.Role.STAFF,
        first_name="Stacy",
        last_name="Staff",
    )
    assert user.company_id is None


@pytest.mark.django_db
def test_client_requires_company_id() -> None:
    with pytest.raises(IntegrityError):
        User.objects.create_user(
            "orphan@example.com",
            "x",
            role=User.Role.CLIENT,
            first_name="Olivia",
            last_name="Orphan",
        )


@pytest.mark.django_db
def test_create_superuser_defaults_to_director() -> None:
    admin_user = User.objects.create_superuser(
        "root@example.com",
        "admin-secret",
        first_name="Root",
        last_name="Admin",
    )
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
    assert admin_user.role == User.Role.DIRECTOR
