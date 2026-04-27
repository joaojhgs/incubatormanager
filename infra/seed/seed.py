"""Seed orchestration — creates test users for integration tests."""

from __future__ import annotations

import os


def main() -> None:
    """Create Director and Client test users for e2e gateway auth tests."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_service.settings")

    try:
        import django

        django.setup()
    except ImportError:
        print("seed: skipping — Django not available in this context")
        return

    from users.models import User

    director_email = "director@ilb.test"
    client_email = "client@ilb.test"
    password = "test-password-1234"
    # Fixed company UUID for the Client test user (required by DB constraint).
    seed_company_id = os.environ.get("SEED_COMPANY_ID", "11111111-1111-4111-8111-111111111111")

    if not User.objects.filter(email=director_email).exists():
        User.objects.create_user(
            director_email,
            password,
            role=User.Role.DIRECTOR,
            first_name="Dir",
            last_name="Ector",
        )
        print(f"seed: created Director user {director_email}")
    else:
        print(f"seed: Director user {director_email} already exists")

    if not User.objects.filter(email=client_email).exists():
        User.objects.create_user(
            client_email,
            password,
            role=User.Role.CLIENT,
            first_name="Cli",
            last_name="Ent",
            company_id=seed_company_id,
        )
        print(f"seed: created Client user {client_email}")
    else:
        print(f"seed: Client user {client_email} already exists")

    print("seed: done")


if __name__ == "__main__":
    main()
