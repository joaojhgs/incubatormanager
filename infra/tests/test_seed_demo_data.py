"""Regression checks for deterministic demo seed data."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = REPO_ROOT / "infra" / "seed" / "seed.py"


def load_seed_module():
    spec = importlib.util.spec_from_file_location("infra_seed", SEED_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PlaceholderCountingCursor:
    """Small cursor fake that verifies SQL placeholders match row values."""

    def __init__(self) -> None:
        self.executed = 0

    def execute(self, sql: str, row: Any = None) -> None:
        if row is not None:
            expected = sql.count("%s")
            actual = len(row) if isinstance(row, tuple) else 1
            assert actual == expected, f"{actual} values for {expected} placeholders in {sql}"
        self.executed += 1

    def fetchone(self) -> tuple[bool]:
        return (True,)


def test_seed_generates_representative_demo_counts() -> None:
    seed = load_seed_module()

    assert len(seed.company_rows()) == 10
    assert len(seed.space_rows()) == 10
    assert len(seed.contract_rows()) == 10
    assert len(seed.booking_rows()) == 10
    assert len(seed.equipment_rows()) == 10
    assert len(seed.ticket_rows()) == 10
    assert len(seed.document_rows()) == 10
    assert len(seed.payment_rows()) == 20
    assert len(seed.employee_rows()) == 20


def test_seed_company_ids_align_with_dev_auth_users() -> None:
    seed = load_seed_module()

    assert tuple(seed.COMPANY_IDS[:3]) == seed.DEV_COMPANY_IDS
    client_companies = {row["company_id"] for row in seed.user_rows() if row["role"] == "Client"}
    assert seed.DEV_COMPANY_IDS[0] in client_companies
    assert seed.DEV_COMPANY_IDS[1] in client_companies
    assert seed.DEV_COMPANY_IDS[2] in client_companies


def test_service_database_url_is_opt_in_on_host(monkeypatch, tmp_path) -> None:
    seed = load_seed_module()
    env_keys = [f"{name.upper()}_DB_PASSWORD" for name in seed.DEFAULT_DB_PASSWORDS]
    env_keys.extend(["DATABASE_URL", "SEED_ENABLE_SERVICE_DATABASES"])
    for key in env_keys:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)

    assert seed.service_database_url("company") is None

    monkeypatch.setenv("SEED_ENABLE_SERVICE_DATABASES", "1")
    assert (
        seed.service_database_url("company")
        == "postgresql://company_svc:company-db-dev@postgres:5432/company_db"
    )


def test_seed_sql_shapes_match_generated_rows() -> None:
    seed = load_seed_module()
    cursor = PlaceholderCountingCursor()

    for name in (
        "seed_company",
        "seed_space",
        "seed_contract",
        "seed_booking",
        "seed_inventory",
        "seed_finance",
        "seed_ticket",
        "seed_dashboard",
        "seed_document",
    ):
        getattr(seed, name)(cursor)

    assert cursor.executed > 0


def test_auth_service_receives_seed_database_passwords() -> None:
    compose = (REPO_ROOT / "infra" / "docker-compose.yml").read_text()
    auth_start = compose.index("  auth-service:")
    auth_end = compose.index("  company-service:")
    auth_block = compose[auth_start:auth_end]

    services = (
        "COMPANY",
        "CONTRACT",
        "FINANCE",
        "SPACE",
        "BOOKING",
        "INVENTORY",
        "TICKET",
        "DASHBOARD",
        "DOCUMENT",
    )
    for service in services:
        assert f"{service}_DB_PASSWORD: ${{{service}_DB_PASSWORD}}" in auth_block
