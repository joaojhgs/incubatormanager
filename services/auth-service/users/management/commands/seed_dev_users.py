"""Create 10 deterministic dev users: 1 Director, 3 Staff, 6 Clients (two per company)."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterable

from django.core.management.base import BaseCommand, CommandError

from users.models import User

# Stable UUIDs for `company_id` (logical refs; align company-service seed with these).
DEV_COMPANY_IDS: tuple[uuid.UUID, ...] = (
    uuid.UUID("11111111-1111-4111-8111-111111111111"),
    uuid.UUID("22222222-2222-4222-8222-222222222222"),
    uuid.UUID("33333333-3333-4333-8333-333333333333"),
)


def _dev_user_specs() -> Iterable[tuple[str, str, str, str, uuid.UUID | None]]:
    """Yield (email, role, first_name, last_name, company_id)."""
    yield ("dev.director@ilb.test", User.Role.DIRECTOR, "Dev", "Director", None)
    yield ("dev.staff1@ilb.test", User.Role.STAFF, "Staff", "One", None)
    yield ("dev.staff2@ilb.test", User.Role.STAFF, "Staff", "Two", None)
    yield ("dev.staff3@ilb.test", User.Role.STAFF, "Staff", "Three", None)
    for comp_idx, company_id in enumerate(DEV_COMPANY_IDS):
        n = comp_idx + 1
        yield (
            f"dev.client.{n}a@ilb.test",
            User.Role.CLIENT,
            "Client",
            f"Co{n}A",
            company_id,
        )
        yield (
            f"dev.client.{n}b@ilb.test",
            User.Role.CLIENT,
            "Client",
            f"Co{n}B",
            company_id,
        )


class Command(BaseCommand):
    help = (
        "Idempotently create 10 dev users (1 Director, 3 Staff, 6 Clients). "
        "Passwords come from AUTH_DEV_SEED_PASSWORD (and optional role overrides); "
        "see .env.example."
    )

    def handle(self, **_options: object) -> None:
        password = os.environ.get("AUTH_DEV_SEED_PASSWORD")
        if not password:
            raise CommandError(
                "AUTH_DEV_SEED_PASSWORD is not set. Add it to your environment or .env file."
            )
        pwd_director = os.environ.get("AUTH_DEV_SEED_DIRECTOR_PASSWORD", password)
        pwd_staff = os.environ.get("AUTH_DEV_SEED_STAFF_PASSWORD", password)
        pwd_client = os.environ.get("AUTH_DEV_SEED_CLIENT_PASSWORD", password)

        for email, role, first_name, last_name, company_id in _dev_user_specs():
            pwd = {
                User.Role.DIRECTOR: pwd_director,
                User.Role.STAFF: pwd_staff,
                User.Role.CLIENT: pwd_client,
            }[role]

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "role": role,
                    "first_name": first_name,
                    "last_name": last_name,
                    "company_id": company_id,
                    "is_active": True,
                },
            )
            user.role = role
            user.first_name = first_name
            user.last_name = last_name
            user.company_id = company_id
            user.is_active = True
            user.set_password(pwd)
            user.save(
                update_fields=[
                    "role",
                    "first_name",
                    "last_name",
                    "company_id",
                    "is_active",
                    "password",
                    "updated_at",
                ]
            )
            action = "created" if created else "updated"
            self.stdout.write(self.style.SUCCESS(f"{action} user {email} ({role})"))

        self.stdout.write(self.style.SUCCESS("seed_dev_users: done"))
