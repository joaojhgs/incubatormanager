"""Seed orchestration for local demo and integration-test data.

The script always keeps the gateway auth smoke users in auth-service, then best-effort seeds
representative cross-service demo rows when it can reach the service databases. It is intentionally
idempotent: all non-auth demo rows use stable UUID primary keys and PostgreSQL upserts.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

DEMO_NAMESPACE = uuid.UUID("7a3226b3-99cb-42ec-8f0d-2f2845f3e031")
DEMO_PASSWORD = "test-password-1234"
DEFAULT_COMPANY_ID = uuid.UUID(
    os.environ.get("SEED_COMPANY_ID", "11111111-1111-4111-8111-111111111111")
)
DEV_COMPANY_IDS: tuple[uuid.UUID, uuid.UUID, uuid.UUID] = (
    DEFAULT_COMPANY_ID,
    uuid.UUID("22222222-2222-4222-8222-222222222222"),
    uuid.UUID("33333333-3333-4333-8333-333333333333"),
)
DEFAULT_DB_PASSWORDS: Mapping[str, str] = {
    "company": "company-db-dev",
    "space": "space-db-dev",
    "contract": "contract-db-dev",
    "finance": "finance-db-dev",
    "booking": "booking-db-dev",
    "inventory": "inventory-db-dev",
    "ticket": "ticket-db-dev",
    "dashboard": "dashboard-db-dev",
    "document": "document-db-dev",
}


def demo_id(kind: str, index: int | str) -> uuid.UUID:
    """Return a stable UUID for a demo entity."""

    return uuid.uuid5(DEMO_NAMESPACE, f"{kind}:{index}")


COMPANY_IDS: tuple[uuid.UUID, ...] = DEV_COMPANY_IDS + tuple(
    demo_id("company", index) for index in range(4, 11)
)
SPACE_IDS: tuple[uuid.UUID, ...] = tuple(demo_id("space", index) for index in range(1, 11))
CONTRACT_IDS: tuple[uuid.UUID, ...] = tuple(demo_id("contract", index) for index in range(1, 11))
BOOKING_IDS: tuple[uuid.UUID, ...] = tuple(demo_id("booking", index) for index in range(1, 11))
EQUIPMENT_IDS: tuple[uuid.UUID, ...] = tuple(demo_id("equipment", index) for index in range(1, 11))
PAYMENT_IDS: tuple[uuid.UUID, ...] = tuple(demo_id("payment", index) for index in range(1, 21))
EMPLOYEE_IDS: tuple[uuid.UUID, ...] = tuple(demo_id("employee", index) for index in range(1, 101))
TICKET_IDS: tuple[uuid.UUID, ...] = tuple(demo_id("ticket", index) for index in range(1, 11))
DOCUMENT_IDS: tuple[uuid.UUID, ...] = tuple(demo_id("document", index) for index in range(1, 11))
STAFF_USER_ID = demo_id("auth-user", "staff")
DIRECTOR_USER_ID = demo_id("auth-user", "director")
CLIENT_USER_IDS: tuple[uuid.UUID, ...] = tuple(
    demo_id("auth-user-client", index) for index in range(1, 11)
)

CAE_ROWS: tuple[tuple[uuid.UUID, str, str], ...] = (
    (demo_id("cae", "0111"), "0111", "Growing of cereals and oil seeds"),
    (demo_id("cae", "1011"), "1011", "Processing and preserving of meat"),
    (demo_id("cae", "1413"), "1413", "Manufacture of other outerwear"),
    (demo_id("cae", "1812"), "1812", "Other printing"),
    (demo_id("cae", "2042"), "2042", "Manufacture of perfumes and preparations"),
    (demo_id("cae", "2611"), "2611", "Manufacture of electronic components"),
    (demo_id("cae", "6201"), "6201", "Computer programming activities"),
    (demo_id("cae", "7022"), "7022", "Management consultancy activities"),
    (demo_id("cae", "7219"), "7219", "Research and development in engineering"),
    (demo_id("cae", "8559"), "8559", "Other education n.e.c."),
)

MATURITY_STAGE_ROWS: tuple[tuple[uuid.UUID, str, Decimal, str, int], ...] = (
    (
        uuid.UUID("11111111-1111-4111-8111-111111111111"),
        "Incubated",
        Decimal("100.00"),
        "Early-stage companies in the incubation program.",
        1,
    ),
    (
        uuid.UUID("22222222-2222-4222-8222-222222222222"),
        "Startup",
        Decimal("250.00"),
        "Startup companies with an established product or service.",
        2,
    ),
    (
        uuid.UUID("33333333-3333-4333-8333-333333333333"),
        "Intermediate",
        Decimal("500.00"),
        "Companies at an intermediate growth stage.",
        3,
    ),
    (
        uuid.UUID("44444444-4444-4444-8444-444444444444"),
        "Consolidated",
        Decimal("900.00"),
        "Established, consolidated companies.",
        4,
    ),
)

SPACE_TYPE_ROWS: tuple[tuple[uuid.UUID, str], ...] = (
    (demo_id("space-type", "office"), "Private office"),
    (demo_id("space-type", "cowork"), "Coworking desk"),
    (demo_id("space-type", "lab"), "Prototype lab"),
    (demo_id("space-type", "meeting"), "Meeting room"),
)

EQUIPMENT_TYPE_ROWS: tuple[tuple[uuid.UUID, str], ...] = (
    (demo_id("equipment-type", "display"), "Display and presentation"),
    (demo_id("equipment-type", "printer"), "Printing and scanning"),
    (demo_id("equipment-type", "network"), "Network kit"),
    (demo_id("equipment-type", "lab"), "Prototype lab kit"),
)


def user_rows() -> tuple[dict[str, Any], ...]:
    return (
        {
            "id": DIRECTOR_USER_ID,
            "email": "director@ilb.test",
            "role": "Director",
            "first_name": "Dir",
            "last_name": "Ector",
            "company_id": None,
        },
        {
            "id": STAFF_USER_ID,
            "email": "staff@ilb.test",
            "role": "Staff",
            "first_name": "Sam",
            "last_name": "Staff",
            "company_id": None,
        },
        {
            "id": CLIENT_USER_IDS[0],
            "email": "client@ilb.test",
            "role": "Client",
            "first_name": "Cli",
            "last_name": "Ent",
            "company_id": COMPANY_IDS[0],
        },
        *(
            {
                "id": CLIENT_USER_IDS[index - 1],
                "email": f"client{index:02d}@ilb.test",
                "role": "Client",
                "first_name": f"Client {index:02d}",
                "last_name": "Contact",
                "company_id": COMPANY_IDS[index - 1],
            }
            for index in range(2, 11)
        ),
    )


def company_rows() -> list[dict[str, Any]]:
    names = (
        "Aster Labs",
        "Blue Forge Analytics",
        "Cedar Robotics",
        "Delta BioMaterials",
        "Eclipse Learning",
        "Faro Mobility",
        "GreenGrid Energy",
        "Helix Medical Devices",
        "Ion Cloud Systems",
        "Juniper Food Tech",
    )
    return [
        {
            "id": company_id,
            "name": name,
            "tax_id": f"PT500000{index:03d}",
            "address": f"ILB Campus, Building {index}",
            "phone": f"+351 210 000 {index:03d}",
            "email": f"demo{index:02d}@ilb.test",
            "legal_representative": f"Demo Representative {index:02d}",
            "cae_id": CAE_ROWS[(index - 1) % len(CAE_ROWS)][0],
            "maturity_stage_id": MATURITY_STAGE_ROWS[(index - 1) % len(MATURITY_STAGE_ROWS)][0],
            "description": f"Representative Phase 2 demo company {index:02d}.",
        }
        for index, (company_id, name) in enumerate(zip(COMPANY_IDS, names, strict=True), start=1)
    ]


def employee_rows() -> list[dict[str, Any]]:
    employee_types = ("Regular", "Intern", "PhD", "Designer", "Junior", "Senior")
    rows: list[dict[str, Any]] = []
    for index, employee_id in enumerate(EMPLOYEE_IDS, start=1):
        company_index = (index - 1) // 10
        company_id = COMPANY_IDS[company_index]
        company_name = company_rows()[company_index]["name"]
        employee_number = (index - 1) % 10 + 1
        rows.append(
            {
                "id": employee_id,
                "company_id": company_id,
                "name": f"{company_name} Employee {employee_number:02d}",
                "type": employee_types[(index + company_index - 1) % len(employee_types)],
                "start_date": date(2024, 1, 1) + timedelta(days=index * 11),
                "end_date": date(2026, 4, 30) if index % 10 == 0 else None,
                "is_active": index % 10 != 0,
            }
        )
    return rows


def space_rows() -> list[dict[str, Any]]:
    statuses = (
        "Occupied",
        "Reserved",
        "Available",
        "Maintenance",
        "Occupied",
        "Available",
        "Blocked",
        "Reserved",
        "Available",
        "Occupied",
    )
    return [
        {
            "id": space_id,
            "name": f"Demo Space {index:02d}",
            "space_type_id": SPACE_TYPE_ROWS[(index - 1) % len(SPACE_TYPE_ROWS)][0],
            "capacity": 2 + (index % 8),
            "rental_cost": Decimal(18 + index * 4).quantize(Decimal("0.01")),
            "rental_cost_unit": "day" if index in (2, 5, 8) else "hour",
            "status": statuses[index - 1],
            "company_id": COMPANY_IDS[index - 1] if statuses[index - 1] == "Occupied" else None,
            "is_active": True,
        }
        for index, space_id in enumerate(SPACE_IDS, start=1)
    ]


def contract_rows() -> list[dict[str, Any]]:
    statuses = (
        "active",
        "active",
        "active",
        "draft",
        "terminated",
        "active",
        "expired",
        "active",
        "draft",
        "active",
    )
    rows: list[dict[str, Any]] = []
    for index, contract_id in enumerate(CONTRACT_IDS, start=1):
        area = Decimal(12 + index * 3).quantize(Decimal("0.01"))
        rate = Decimal((100, 250, 500, 900)[(index - 1) % 4]).quantize(Decimal("0.01"))
        rows.append(
            {
                "id": contract_id,
                "company_id": COMPANY_IDS[index - 1],
                "space_id": SPACE_IDS[index - 1],
                "area_sqm": area,
                "rate_per_sqm": rate,
                "monthly_fee": area * rate,
                "start_date": date(2025, 1, 1) + timedelta(days=index * 14),
                "end_date": date(2026, 12, 31) + timedelta(days=index * 14),
                "status": statuses[index - 1],
                "termination_reason": "Demo early exit"
                if statuses[index - 1] == "terminated"
                else "",
            }
        )
    return rows


def booking_rows() -> list[dict[str, Any]]:
    statuses = (
        "Pending",
        "Approved",
        "Rejected",
        "Cancelled",
        "Completed",
        "Approved",
        "Pending",
        "Completed",
        "Approved",
        "Pending",
    )
    start = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
    rows: list[dict[str, Any]] = []
    for index, booking_id in enumerate(BOOKING_IDS, start=1):
        starts_at = start + timedelta(days=index, hours=index % 5)
        rows.append(
            {
                "id": booking_id,
                "company_id": COMPANY_IDS[index - 1],
                "space_id": SPACE_IDS[index - 1],
                "created_by_user_id": CLIENT_USER_IDS[index - 1],
                "created_by_role": "Client",
                "is_public": index in (3, 8),
                "requester_name": f"Demo Requester {index:02d}",
                "requester_email": f"requester{index:02d}@ilb.test",
                "requester_phone": f"+351 930 000 {index:03d}",
                "start_time": starts_at,
                "end_time": starts_at + timedelta(hours=2 + (index % 3)),
                "quoted_price": Decimal(40 + index * 15).quantize(Decimal("0.01")),
                "equipment_ids": [str(EQUIPMENT_IDS[index - 1])],
                "status": statuses[index - 1],
                "notes": f"Representative demo booking {index:02d}.",
            }
        )
    return rows


def equipment_rows() -> list[dict[str, Any]]:
    statuses = (
        "Available",
        "In use",
        "Available",
        "Maintenance",
        "In use",
        "Available",
        "Available",
        "In use",
        "Maintenance",
        "Available",
    )
    return [
        {
            "id": equipment_id,
            "name": f"Demo Equipment {index:02d}",
            "equipment_type_id": EQUIPMENT_TYPE_ROWS[(index - 1) % len(EQUIPMENT_TYPE_ROWS)][0],
            "serial_number": f"ILB-DEMO-{index:04d}",
            "assigned_space_id": SPACE_IDS[index - 1] if statuses[index - 1] == "In use" else None,
            "rental_cost": Decimal(12 + index * 3).quantize(Decimal("0.01")),
            "rental_cost_unit": (
                "fixed" if index in (4, 9) else ("day" if index in (2, 6) else "hour")
            ),
            "status": statuses[index - 1],
            "notes": f"Seeded demo inventory item {index:02d}.",
            "is_active": True,
        }
        for index, equipment_id in enumerate(EQUIPMENT_IDS, start=1)
    ]


def payment_rows() -> list[dict[str, Any]]:
    statuses = (
        "paid",
        "pending",
        "overdue",
        "paid",
        "pending",
        "paid",
        "overdue",
        "pending",
        "paid",
        "pending",
    )
    rows: list[dict[str, Any]] = []
    today = date(2026, 5, 25)
    for index, contract in enumerate(contract_rows(), start=1):
        rows.append(
            {
                "id": PAYMENT_IDS[index - 1],
                "company_id": contract["company_id"],
                "contract_id": contract["id"],
                "booking_id": None,
                "source": "contract",
                "payment_type": "monthly",
                "amount": contract["monthly_fee"],
                "currency": "EUR",
                "status": statuses[index - 1],
                "due_date": today.replace(day=1) + timedelta(days=index - 1),
                "paid_at": datetime(2026, 5, min(index + 1, 25), 11, 30, tzinfo=UTC)
                if statuses[index - 1] == "paid"
                else None,
                "period_start": date(2026, 5, 1),
                "period_end": date(2026, 5, 31),
                "reference_id": f"DEMO-CONTRACT-{index:02d}",
            }
        )
    for index, booking in enumerate(booking_rows(), start=1):
        payment_index = index + 10
        rows.append(
            {
                "id": PAYMENT_IDS[payment_index - 1],
                "company_id": booking["company_id"],
                "contract_id": None,
                "booking_id": booking["id"],
                "source": "booking",
                "payment_type": "rental",
                "amount": booking["quoted_price"],
                "currency": "EUR",
                "status": statuses[(index + 2) % len(statuses)],
                "due_date": today + timedelta(days=index),
                "paid_at": datetime(2026, 5, min(index + 10, 25), 15, 0, tzinfo=UTC)
                if statuses[(index + 2) % len(statuses)] == "paid"
                else None,
                "period_start": None,
                "period_end": None,
                "reference_id": f"DEMO-BOOKING-{index:02d}",
            }
        )
    return rows


def ticket_rows() -> list[dict[str, Any]]:
    statuses = (
        "Open",
        "In progress",
        "Waiting response",
        "Resolved",
        "Closed",
        "Open",
        "In progress",
        "Resolved",
        "Open",
        "Waiting response",
    )
    return [
        {
            "id": ticket_id,
            "company_id": COMPANY_IDS[index - 1],
            "subject": f"Demo support request {index:02d}",
            "description": f"Representative ticket for operational demo flow {index:02d}.",
            "status": statuses[index - 1],
            "assigned_to": STAFF_USER_ID if index % 2 == 0 else None,
            "created_by_user_id": CLIENT_USER_IDS[index - 1],
            "created_by_role": "Client",
        }
        for index, ticket_id in enumerate(TICKET_IDS, start=1)
    ]


def document_rows() -> list[dict[str, Any]]:
    entity_kinds = ("Company", "Contract", "Booking")
    entity_ids = (COMPANY_IDS, CONTRACT_IDS, BOOKING_IDS)
    rows: list[dict[str, Any]] = []
    for index, document_id in enumerate(DOCUMENT_IDS, start=1):
        entity_index = (index - 1) % len(entity_kinds)
        entity_type = entity_kinds[entity_index]
        entity_id = entity_ids[entity_index][index - 1]
        rows.append(
            {
                "id": document_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "file_name": f"demo-{entity_type.lower()}-{index:02d}.pdf",
                "file_path": f"demo/{entity_type.lower()}/{index:02d}.pdf",
                "file_size": 2048 + index * 137,
                "mime_type": "application/pdf",
                "description": f"Demo {entity_type.lower()} evidence document {index:02d}.",
                "uploaded_by": STAFF_USER_ID,
                "is_active": True,
            }
        )
    return rows


def seed_auth_users() -> dict[str, uuid.UUID]:
    """Create/update deterministic auth users required by e2e and local demos."""

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_service.settings")

    try:
        import django

        django.setup()
    except ImportError:
        print("seed: auth skipped — Django not available in this context")
        return {str(row["email"]): row["id"] for row in user_rows()}

    from users.models import User

    user_ids: dict[str, uuid.UUID] = {}
    for row in user_rows():
        email = str(row["email"])
        user = User.objects.filter(email=email).first()
        created = user is None
        if user is None:
            user = User.objects.create_user(
                email,
                DEMO_PASSWORD,
                id=row["id"],
                role=row["role"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                company_id=row["company_id"],
            )
        else:
            user.role = row["role"]
            user.first_name = row["first_name"]
            user.last_name = row["last_name"]
            user.company_id = row["company_id"]
            user.is_active = True
        user.set_password(DEMO_PASSWORD)
        user.save(
            update_fields=(
                "role",
                "first_name",
                "last_name",
                "company_id",
                "is_active",
                "password",
                "updated_at",
            )
        )
        user_ids[email] = user.id
        action = "created" if created else "updated"
        print(f"seed: {action} {row['role']} user {email}")

    return user_ids


def service_database_url(service: str) -> str | None:
    """Return a database URL for a service, using env overrides or local-demo defaults."""

    env_prefix = service.upper().replace("-", "_")
    explicit_url = os.environ.get(f"SEED_{env_prefix}_DATABASE_URL") or os.environ.get(
        f"{env_prefix}_DATABASE_URL"
    )
    if explicit_url:
        return explicit_url

    if not (os.environ.get("SEED_ENABLE_SERVICE_DATABASES") or os.getcwd() == "/app"):
        return None

    password = os.environ.get(f"{env_prefix}_DB_PASSWORD") or DEFAULT_DB_PASSWORDS.get(service)
    if not password:
        return None

    host = os.environ.get("SEED_DB_HOST", "postgres")
    port = os.environ.get("SEED_DB_PORT", "5432")
    return f"postgresql://{service}_svc:{password}@{host}:{port}/{service}_db"


def table_exists(cursor: Any, table_name: str) -> bool:
    cursor.execute("SELECT to_regclass(%s)", (table_name,))
    return cursor.fetchone()[0] is not None


def require_tables(cursor: Any, service: str, table_names: Sequence[str]) -> bool:
    missing = [table_name for table_name in table_names if not table_exists(cursor, table_name)]
    if missing:
        print(f"seed: {service} skipped — missing migrated tables: {', '.join(missing)}")
        return False
    return True


def run_many(cursor: Any, sql: str, rows: Iterable[Sequence[Any]]) -> int:
    count = 0
    for row in rows:
        cursor.execute(sql, row)
        count += 1
    return count


def run_service_seed(service: str, table_names: Sequence[str], seed_fn: Any) -> None:
    url = service_database_url(service)
    if not url:
        print(f"seed: {service} skipped — database URL unavailable")
        return

    try:
        import psycopg
    except ImportError:
        print(f"seed: {service} skipped — psycopg not available in this context")
        return

    try:
        with psycopg.connect(url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                if require_tables(cursor, service, table_names):
                    seed_fn(cursor)
            connection.commit()
    except psycopg.OperationalError as exc:
        print(f"seed: {service} skipped — database unavailable ({exc.__class__.__name__})")


def seed_company(cursor: Any) -> None:
    count = run_many(
        cursor,
        """
        INSERT INTO core_cae (id, code, description)
        VALUES (%s, %s, %s)
        ON CONFLICT (code) DO UPDATE SET
            id = EXCLUDED.id,
            description = EXCLUDED.description
        """,
        CAE_ROWS,
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_maturitystage (id, name, rate_per_sqm, description, display_order)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET
            id = EXCLUDED.id,
            rate_per_sqm = EXCLUDED.rate_per_sqm,
            description = EXCLUDED.description,
            display_order = EXCLUDED.display_order
        """,
        MATURITY_STAGE_ROWS,
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_company (
            id, name, tax_id, address, phone, email, legal_representative, cae_id,
            maturity_stage_id, description, is_active, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), NOW())
        ON CONFLICT (tax_id) DO UPDATE SET
            name = EXCLUDED.name,
            address = EXCLUDED.address,
            phone = EXCLUDED.phone,
            email = EXCLUDED.email,
            legal_representative = EXCLUDED.legal_representative,
            cae_id = EXCLUDED.cae_id,
            maturity_stage_id = EXCLUDED.maturity_stage_id,
            description = EXCLUDED.description,
            is_active = TRUE,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["name"],
                row["tax_id"],
                row["address"],
                row["phone"],
                row["email"],
                row["legal_representative"],
                row["cae_id"],
                row["maturity_stage_id"],
                row["description"],
            )
            for row in company_rows()
        ),
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_employee (
            id, company_id, name, type, start_date, end_date, is_active, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            name = EXCLUDED.name,
            type = EXCLUDED.type,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["company_id"],
                row["name"],
                row["type"],
                row["start_date"],
                row["end_date"],
                row["is_active"],
            )
            for row in employee_rows()
        ),
    )
    print(f"seed: company upserted {count} rows")


def seed_space(cursor: Any) -> None:
    count = run_many(
        cursor,
        """
        INSERT INTO core_spacetype (id, name, is_active, created_at, updated_at)
        VALUES (%s, %s, TRUE, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, is_active = TRUE, updated_at = NOW()
        """,
        SPACE_TYPE_ROWS,
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_space (
            id, name, space_type_id, capacity, rental_cost, rental_cost_unit, status,
            company_id, is_active, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            space_type_id = EXCLUDED.space_type_id,
            capacity = EXCLUDED.capacity,
            rental_cost = EXCLUDED.rental_cost,
            rental_cost_unit = EXCLUDED.rental_cost_unit,
            status = EXCLUDED.status,
            company_id = EXCLUDED.company_id,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["name"],
                row["space_type_id"],
                row["capacity"],
                row["rental_cost"],
                row["rental_cost_unit"],
                row["status"],
                row["company_id"],
                row["is_active"],
            )
            for row in space_rows()
        ),
    )
    count += run_many(
        cursor,
        """
        UPDATE core_space
        SET rental_cost = %s,
            rental_cost_unit = %s,
            updated_at = NOW()
        WHERE id = %s
          AND (rental_cost IS NULL OR rental_cost_unit IS NULL)
        """,
        (
            (Decimal("18.00"), "hour", "22222222-2222-4222-8222-222222222201"),
            (Decimal("95.00"), "day", "22222222-2222-4222-8222-222222222202"),
            (Decimal("30.00"), "hour", "22222222-2222-4222-8222-222222222203"),
        ),
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_spacecontract (
            id, contract_id, company_id, space_id, status, area_sqm, rate_per_sqm,
            monthly_fee, start_date, end_date, termination_reason, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (contract_id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            space_id = EXCLUDED.space_id,
            status = EXCLUDED.status,
            area_sqm = EXCLUDED.area_sqm,
            rate_per_sqm = EXCLUDED.rate_per_sqm,
            monthly_fee = EXCLUDED.monthly_fee,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            termination_reason = EXCLUDED.termination_reason,
            updated_at = NOW()
        """,
        (
            (
                demo_id("space-contract", row["id"]),
                row["id"],
                row["company_id"],
                row["space_id"],
                row["status"].title() if row["status"] != "draft" else "Active",
                row["area_sqm"],
                row["rate_per_sqm"],
                row["monthly_fee"],
                row["start_date"],
                row["end_date"],
                row["termination_reason"],
            )
            for row in contract_rows()
            if row["status"] != "draft"
        ),
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_spacebookingrecord (
            id, booking_id, space_id, company_id, status, start_time, end_time,
            quoted_price, equipment_ids, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW(), NOW())
        ON CONFLICT (booking_id) DO UPDATE SET
            space_id = EXCLUDED.space_id,
            company_id = EXCLUDED.company_id,
            status = EXCLUDED.status,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            quoted_price = EXCLUDED.quoted_price,
            equipment_ids = EXCLUDED.equipment_ids,
            updated_at = NOW()
        """,
        (
            (
                demo_id("space-booking", row["id"]),
                row["id"],
                row["space_id"],
                row["company_id"],
                row["status"],
                row["start_time"],
                row["end_time"],
                row["quoted_price"],
                json.dumps(row["equipment_ids"]),
            )
            for row in booking_rows()
            if row["status"] in {"Approved", "Rejected", "Cancelled", "Completed"}
        ),
    )
    print(f"seed: space upserted {count} rows")


def seed_contract(cursor: Any) -> None:
    count = run_many(
        cursor,
        """
        INSERT INTO core_contract (
            id, company_id, space_id, area_sqm, rate_per_sqm, monthly_fee, start_date,
            end_date, status, termination_reason, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            space_id = EXCLUDED.space_id,
            area_sqm = EXCLUDED.area_sqm,
            rate_per_sqm = EXCLUDED.rate_per_sqm,
            monthly_fee = EXCLUDED.monthly_fee,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            status = EXCLUDED.status,
            termination_reason = EXCLUDED.termination_reason,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["company_id"],
                row["space_id"],
                row["area_sqm"],
                row["rate_per_sqm"],
                row["monthly_fee"],
                row["start_date"],
                row["end_date"],
                row["status"],
                row["termination_reason"],
            )
            for row in contract_rows()
        ),
    )
    print(f"seed: contract upserted {count} rows")


def seed_booking(cursor: Any) -> None:
    count = run_many(
        cursor,
        """
        INSERT INTO core_booking (
            id, company_id, space_id, created_by_user_id, created_by_role, is_public,
            requester_name, requester_email, requester_phone, start_time, end_time,
            quoted_price, equipment_ids, status, notes, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            space_id = EXCLUDED.space_id,
            created_by_user_id = EXCLUDED.created_by_user_id,
            created_by_role = EXCLUDED.created_by_role,
            is_public = EXCLUDED.is_public,
            requester_name = EXCLUDED.requester_name,
            requester_email = EXCLUDED.requester_email,
            requester_phone = EXCLUDED.requester_phone,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            quoted_price = EXCLUDED.quoted_price,
            equipment_ids = EXCLUDED.equipment_ids,
            status = EXCLUDED.status,
            notes = EXCLUDED.notes,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["company_id"],
                row["space_id"],
                row["created_by_user_id"],
                row["created_by_role"],
                row["is_public"],
                row["requester_name"],
                row["requester_email"],
                row["requester_phone"],
                row["start_time"],
                row["end_time"],
                row["quoted_price"],
                json.dumps(row["equipment_ids"]),
                row["status"],
                row["notes"],
            )
            for row in booking_rows()
        ),
    )
    print(f"seed: booking upserted {count} rows")


def seed_inventory(cursor: Any) -> None:
    count = run_many(
        cursor,
        """
        INSERT INTO core_equipmenttype (id, name, is_active, created_at, updated_at)
        VALUES (%s, %s, TRUE, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, is_active = TRUE, updated_at = NOW()
        """,
        EQUIPMENT_TYPE_ROWS,
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_equipment (
            id, name, equipment_type_id, serial_number, assigned_space_id, rental_cost,
            rental_cost_unit,
            status, notes, is_active, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            equipment_type_id = EXCLUDED.equipment_type_id,
            serial_number = EXCLUDED.serial_number,
            assigned_space_id = EXCLUDED.assigned_space_id,
            rental_cost = EXCLUDED.rental_cost,
            rental_cost_unit = EXCLUDED.rental_cost_unit,
            status = EXCLUDED.status,
            notes = EXCLUDED.notes,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["name"],
                row["equipment_type_id"],
                row["serial_number"],
                row["assigned_space_id"],
                row["rental_cost"],
                row["rental_cost_unit"],
                row["status"],
                row["notes"],
                row["is_active"],
            )
            for row in equipment_rows()
        ),
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_equipmentassignment (
            id, equipment_id, booking_id, company_id, assigned_space_id, status,
            created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (equipment_id, booking_id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            assigned_space_id = EXCLUDED.assigned_space_id,
            status = EXCLUDED.status,
            updated_at = NOW()
        """,
        (
            (
                demo_id("equipment-assignment", row["id"]),
                row["id"],
                BOOKING_IDS[index - 1],
                COMPANY_IDS[index - 1],
                SPACE_IDS[index - 1],
                "Assigned" if index % 4 else "Released",
            )
            for index, row in enumerate(equipment_rows(), start=1)
        ),
    )
    print(f"seed: inventory upserted {count} rows")


def seed_finance(cursor: Any) -> None:
    contracts = contract_rows()
    count = run_many(
        cursor,
        """
        INSERT INTO core_billingcontract (
            id, contract_id, company_id, space_id, area_sqm, rate_per_sqm, monthly_fee,
            start_date, end_date, is_active, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (contract_id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            space_id = EXCLUDED.space_id,
            area_sqm = EXCLUDED.area_sqm,
            rate_per_sqm = EXCLUDED.rate_per_sqm,
            monthly_fee = EXCLUDED.monthly_fee,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        """,
        (
            (
                demo_id("billing-contract", row["id"]),
                row["id"],
                row["company_id"],
                row["space_id"],
                row["area_sqm"],
                row["rate_per_sqm"],
                row["monthly_fee"],
                row["start_date"],
                row["end_date"],
                row["status"] == "active",
            )
            for row in contracts
        ),
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_payment (
            id, company_id, contract_id, booking_id, source, payment_type, amount, currency, status,
            due_date, paid_at, period_start, period_end, reference_id, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            contract_id = EXCLUDED.contract_id,
            booking_id = EXCLUDED.booking_id,
            source = EXCLUDED.source,
            payment_type = EXCLUDED.payment_type,
            amount = EXCLUDED.amount,
            currency = EXCLUDED.currency,
            status = EXCLUDED.status,
            due_date = EXCLUDED.due_date,
            paid_at = EXCLUDED.paid_at,
            period_start = EXCLUDED.period_start,
            period_end = EXCLUDED.period_end,
            reference_id = EXCLUDED.reference_id,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["company_id"],
                row["contract_id"],
                row["booking_id"],
                row["source"],
                row["payment_type"],
                row["amount"],
                row["currency"],
                row["status"],
                row["due_date"],
                row["paid_at"],
                row["period_start"],
                row["period_end"],
                row["reference_id"],
            )
            for row in payment_rows()
        ),
    )
    print(f"seed: finance upserted {count} rows")


def seed_ticket(cursor: Any) -> None:
    count = run_many(
        cursor,
        """
        INSERT INTO core_ticket (
            id, company_id, subject, description, status, assigned_to, created_by_user_id,
            created_by_role, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            subject = EXCLUDED.subject,
            description = EXCLUDED.description,
            status = EXCLUDED.status,
            assigned_to = EXCLUDED.assigned_to,
            created_by_user_id = EXCLUDED.created_by_user_id,
            created_by_role = EXCLUDED.created_by_role,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["company_id"],
                row["subject"],
                row["description"],
                row["status"],
                row["assigned_to"],
                row["created_by_user_id"],
                row["created_by_role"],
            )
            for row in ticket_rows()
        ),
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_ticketmessage (
            id, ticket_id, author_user_id, author_role, content, created_at
        )
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (id) DO UPDATE SET
            ticket_id = EXCLUDED.ticket_id,
            author_user_id = EXCLUDED.author_user_id,
            author_role = EXCLUDED.author_role,
            content = EXCLUDED.content
        """,
        (
            (
                demo_id("ticket-message", f"{ticket_id}:{message_index}"),
                ticket_id,
                STAFF_USER_ID if message_index == 2 else CLIENT_USER_IDS[index - 1],
                "Staff" if message_index == 2 else "Client",
                f"Demo ticket {index:02d} message {message_index}: seeded support conversation.",
            )
            for index, ticket_id in enumerate(TICKET_IDS, start=1)
            for message_index in (1, 2)
        ),
    )
    print(f"seed: ticket upserted {count} rows")


def seed_dashboard(cursor: Any) -> None:
    companies = company_rows()
    contracts = contract_rows()
    bookings = booking_rows()
    payments = payment_rows()
    count = run_many(
        cursor,
        """
        INSERT INTO core_companyprojection (
            company_id, name, cae_code, maturity_stage_name, is_active, archived_at,
            created_at, updated_at
        ) VALUES (%s, %s, %s, %s, TRUE, NULL, NOW(), NOW())
        ON CONFLICT (company_id) DO UPDATE SET
            name = EXCLUDED.name,
            cae_code = EXCLUDED.cae_code,
            maturity_stage_name = EXCLUDED.maturity_stage_name,
            is_active = TRUE,
            archived_at = NULL,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["name"],
                CAE_ROWS[(index - 1) % len(CAE_ROWS)][1],
                MATURITY_STAGE_ROWS[(index - 1) % len(MATURITY_STAGE_ROWS)][1],
            )
            for index, row in enumerate(companies, start=1)
        ),
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_employeeprojection (
            employee_id, company_id, employee_type, is_active, updated_at
        )
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (employee_id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            employee_type = EXCLUDED.employee_type,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        """,
        ((row["id"], row["company_id"], row["type"], row["is_active"]) for row in employee_rows()),
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_contractprojection (
            contract_id, company_id, space_id, area_sqm, rate_per_sqm, monthly_fee,
            start_date, end_date, status, is_active, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (contract_id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            space_id = EXCLUDED.space_id,
            area_sqm = EXCLUDED.area_sqm,
            rate_per_sqm = EXCLUDED.rate_per_sqm,
            monthly_fee = EXCLUDED.monthly_fee,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            status = EXCLUDED.status,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["company_id"],
                row["space_id"],
                row["area_sqm"],
                row["rate_per_sqm"],
                row["monthly_fee"],
                row["start_date"],
                row["end_date"],
                row["status"],
                row["status"] == "active",
            )
            for row in contracts
        ),
    )
    count += run_many(
        cursor,
        """
        INSERT INTO core_bookingprojection (
            booking_id, company_id, space_id, status, quoted_price, start_time, end_time, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (booking_id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            space_id = EXCLUDED.space_id,
            status = EXCLUDED.status,
            quoted_price = EXCLUDED.quoted_price,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["company_id"],
                row["space_id"],
                row["status"],
                row["quoted_price"],
                row["start_time"],
                row["end_time"],
            )
            for row in bookings
        ),
    )
    paid_payments = [row for row in payments if row["status"] == "paid"]
    count += run_many(
        cursor,
        """
        INSERT INTO core_paymentprojection (
            payment_id, company_id, contract_id, booking_id, amount, paid_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (payment_id) DO UPDATE SET
            company_id = EXCLUDED.company_id,
            contract_id = EXCLUDED.contract_id,
            booking_id = EXCLUDED.booking_id,
            amount = EXCLUDED.amount,
            paid_at = EXCLUDED.paid_at,
            updated_at = NOW()
        """,
        (
            (
                row["id"],
                row["company_id"],
                row["contract_id"],
                row["booking_id"],
                row["amount"],
                row["paid_at"],
            )
            for row in paid_payments
        ),
    )
    snapshot = {
        "companies": len(companies),
        "employees": len(employee_rows()),
        "contracts": len(contracts),
        "bookings": len(bookings),
        "payments": len(payments),
        "source": "infra.seed.demo",
    }
    cursor.execute(
        """
        INSERT INTO core_dashboardsnapshot (source, payload, refreshed_at)
        VALUES ('demo-seed', %s::jsonb, NOW())
        ON CONFLICT (source) DO UPDATE SET payload = EXCLUDED.payload, refreshed_at = NOW()
        """,
        (json.dumps(snapshot),),
    )
    count += 1
    print(f"seed: dashboard upserted {count} rows")


def seed_document(cursor: Any) -> None:
    count = run_many(
        cursor,
        """
        INSERT INTO core_document (
            id, entity_type, entity_id, file_name, file_path, file_size, mime_type,
            description, uploaded_by, uploaded_at, is_active
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        ON CONFLICT (id) DO UPDATE SET
            entity_type = EXCLUDED.entity_type,
            entity_id = EXCLUDED.entity_id,
            file_name = EXCLUDED.file_name,
            file_path = EXCLUDED.file_path,
            file_size = EXCLUDED.file_size,
            mime_type = EXCLUDED.mime_type,
            description = EXCLUDED.description,
            uploaded_by = EXCLUDED.uploaded_by,
            is_active = EXCLUDED.is_active
        """,
        (
            (
                row["id"],
                row["entity_type"],
                row["entity_id"],
                row["file_name"],
                row["file_path"],
                row["file_size"],
                row["mime_type"],
                row["description"],
                row["uploaded_by"],
                row["is_active"],
            )
            for row in document_rows()
        ),
    )
    print(f"seed: document upserted {count} rows")


def main() -> None:
    """Seed auth users and best-effort representative demo rows across services."""

    seed_auth_users()
    service_plan = (
        ("company", ("core_company", "core_employee"), seed_company),
        (
            "space",
            ("core_space", "core_spacetype", "core_spacecontract", "core_spacebookingrecord"),
            seed_space,
        ),
        ("contract", ("core_contract",), seed_contract),
        ("booking", ("core_booking",), seed_booking),
        ("inventory", ("core_equipment", "core_equipmentassignment"), seed_inventory),
        ("finance", ("core_billingcontract", "core_payment"), seed_finance),
        ("ticket", ("core_ticket", "core_ticketmessage"), seed_ticket),
        (
            "dashboard",
            (
                "core_companyprojection",
                "core_employeeprojection",
                "core_contractprojection",
                "core_bookingprojection",
                "core_paymentprojection",
                "core_dashboardsnapshot",
            ),
            seed_dashboard,
        ),
        ("document", ("core_document",), seed_document),
    )
    for service, table_names, seed_fn in service_plan:
        run_service_seed(service, table_names, seed_fn)

    print("seed: done")


if __name__ == "__main__":
    main()
