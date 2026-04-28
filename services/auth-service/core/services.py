"""Domain logic for user administration (Director-only HTTP surface)."""

from __future__ import annotations

import uuid
from typing import Any

from django.db import IntegrityError
from django.db.models import QuerySet
from users.models import User


class UserNotFound(Exception):
    """No ``User`` row for the given primary key."""


class DuplicateUserEmail(Exception):
    """Violates unique constraint on ``email``."""


def list_users() -> QuerySet[User]:
    return User.objects.all().order_by("email")


def get_user(user_id: uuid.UUID) -> User:
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise UserNotFound from exc


def create_user(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str,
    company_id: uuid.UUID | None,
) -> User:
    try:
        return User.objects.create_user(
            email,
            password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            company_id=company_id,
        )
    except IntegrityError as exc:
        raise DuplicateUserEmail from exc


def update_user(instance: User, partial: dict[str, Any]) -> User:
    allowed = {"first_name", "last_name", "role", "company_id", "is_active"}
    for key, value in partial.items():
        if key in allowed:
            setattr(instance, key, value)
    if instance.role != User.Role.CLIENT:
        instance.company_id = None
    instance.full_clean()
    try:
        instance.save()
    except IntegrityError as exc:
        raise DuplicateUserEmail from exc
    return instance


def soft_delete_user(instance: User) -> None:
    if not instance.is_active:
        return
    instance.is_active = False
    instance.save(update_fields=["is_active"])
