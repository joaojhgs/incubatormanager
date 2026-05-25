from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "infra" / "docker-compose.yml"
RABBITMQ_DEFINITIONS = ROOT / "infra" / "docker" / "rabbitmq" / "definitions.json"
RABBITMQ_CONFIG = ROOT / "infra" / "docker" / "rabbitmq" / "rabbitmq.conf"
MAKEFILE = ROOT / "Makefile"


DEAD_LETTER_EXCHANGE = "incubator.events.dead-letter"


EXPECTED_BINDINGS = {
    "finance.contract-events": {
        "contract.activated",
        "contract.expired",
        "contract.terminated",
        "booking.approved",
    },
    "space.domain-events": {
        "contract.activated",
        "contract.expired",
        "contract.terminated",
        "booking.approved",
        "booking.rejected",
        "booking.cancelled",
        "booking.completed",
    },
    "inventory.booking-events": {
        "booking.approved",
        "booking.rejected",
        "booking.cancelled",
        "booking.completed",
    },
    "dashboard.domain-events": {
        "company.created",
        "company.archived",
        "employee.changed",
        "contract.activated",
        "contract.expired",
        "contract.terminated",
        "booking.approved",
        "booking.rejected",
        "booking.cancelled",
        "booking.completed",
        "payment.recorded",
    },
}


EXPECTED_SIDECARS = {
    "contract-scheduler": [
        "dockerfile: services/contract-service/Dockerfile",
        "DATABASE_URL: postgresql://contract_svc:",
        "volumes: *scheduler-volumes",
        "/app/infra/cron/contract.crontab",
    ],
    "finance-consumer": [
        "dockerfile: services/finance-service/Dockerfile",
        "DATABASE_URL: postgresql://finance_svc:",
        "command: ['python', 'manage.py', 'consume_finance_events']",
        "depends_on: *consumer-deps",
    ],
    "finance-scheduler": [
        "dockerfile: services/finance-service/Dockerfile",
        "DATABASE_URL: postgresql://finance_svc:",
        "volumes: *scheduler-volumes",
        "/app/infra/cron/finance.crontab",
    ],
    "space-consumer": [
        "dockerfile: services/space-service/Dockerfile",
        "DATABASE_URL: postgresql://space_svc:",
        "command: ['python', 'manage.py', 'consume_space_events']",
        "depends_on: *consumer-deps",
    ],
    "booking-scheduler": [
        "dockerfile: services/booking-service/Dockerfile",
        "DATABASE_URL: postgresql://booking_svc:",
        "volumes: *scheduler-volumes",
        "/app/infra/cron/booking.crontab",
    ],
    "inventory-consumer": [
        "dockerfile: services/inventory-service/Dockerfile",
        "DATABASE_URL: postgresql://inventory_svc:",
        "command: ['python', 'manage.py', 'consume_inventory_events']",
        "depends_on: *consumer-deps",
    ],
    "dashboard-consumer": [
        "dockerfile: services/dashboard-service/Dockerfile",
        "DATABASE_URL: postgresql://dashboard_svc:",
        "command: ['python', 'manage.py', 'consume_dashboard_events']",
        "depends_on: *consumer-deps",
    ],
}


def _compose_config(*, with_project_directory: bool) -> dict[str, object]:
    cmd = [
        "docker",
        "compose",
        "--env-file",
        ".env.example",
    ]
    if with_project_directory:
        cmd.extend(["--project-directory", "."])
    cmd.extend(["-f", "infra/docker-compose.yml", "config", "--format", "json"])
    env = os.environ.copy()
    env.pop("COMPOSE_REPO_ROOT", None)
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def _compose_service_block(compose_text: str, service_name: str) -> str:
    next_service_or_volumes = r"(?=^  [-a-z0-9]+:|^volumes:)"
    pattern = rf"^  {re.escape(service_name)}:\n(?P<body>.*?){next_service_or_volumes}"
    match = re.search(pattern, compose_text, re.M | re.S)
    assert match is not None, f"missing compose service {service_name}"
    return match.group("body")


def test_rabbitmq_definitions_include_runtime_consumer_queues_and_bindings() -> None:
    definitions = json.loads(RABBITMQ_DEFINITIONS.read_text())

    queue_names = {queue["name"] for queue in definitions["queues"]}
    assert set(EXPECTED_BINDINGS).issubset(queue_names)

    bindings_by_destination: dict[str, set[str]] = {
        queue: set() for queue in EXPECTED_BINDINGS
    }
    for binding in definitions["bindings"]:
        destination = binding["destination"]
        if destination in bindings_by_destination:
            assert binding["source"] == "incubator.events"
            assert binding["destination_type"] == "queue"
            bindings_by_destination[destination].add(binding["routing_key"])

    assert bindings_by_destination == EXPECTED_BINDINGS




def test_rabbitmq_definitions_dead_letter_failed_consumer_messages() -> None:
    definitions = json.loads(RABBITMQ_DEFINITIONS.read_text())
    exchange_names = {exchange["name"] for exchange in definitions["exchanges"]}
    assert DEAD_LETTER_EXCHANGE in exchange_names

    queue_by_name = {queue["name"]: queue for queue in definitions["queues"]}
    for queue_name in EXPECTED_BINDINGS:
        dead_letter_queue = f"{queue_name}.dead-letter"
        assert dead_letter_queue in queue_by_name
        assert queue_by_name[queue_name]["arguments"] == {}
        policies = [
            policy
            for policy in definitions.get("policies", [])
            if policy["pattern"] == f"^{queue_name}$"
        ]
        assert policies == [
            {
                "name": f"{queue_name}.dead-letter-policy",
                "vhost": "/",
                "pattern": f"^{queue_name}$",
                "apply-to": "queues",
                "definition": {
                    "dead-letter-exchange": DEAD_LETTER_EXCHANGE,
                    "dead-letter-routing-key": dead_letter_queue,
                },
                "priority": 10,
            }
        ]
        assert any(
            binding["source"] == DEAD_LETTER_EXCHANGE
            and binding["destination"] == dead_letter_queue
            and binding["routing_key"] == dead_letter_queue
            for binding in definitions["bindings"]
        )


def test_compose_declares_consumer_and_scheduler_sidecars() -> None:
    compose_text = COMPOSE.read_text()

    for service_name, expected_fragments in EXPECTED_SIDECARS.items():
        block = _compose_service_block(compose_text, service_name)
        for fragment in expected_fragments:
            assert fragment in block, f"{service_name} missing {fragment}"
        assert "restart: unless-stopped" in block


def test_makefile_local_gate_seed_and_demo_cover_runtime_checks() -> None:
    makefile = MAKEFILE.read_text()

    assert "COMPOSE_ENV_FILE := $(if $(wildcard .env),.env,.env.example)" in makefile
    assert "seed: ## Load deterministic local demo users and smoke fixtures" in makefile
    assert "python manage.py seed_dev_users" in makefile
    assert "python /app/infra/seed/seed.py" in makefile
    assert "demo: ## Reset DBs, seed, and run the stack in the foreground" in makefile
    assert "$(COMPOSE) up -d --build --wait" in makefile
    assert "local-gate: ## Validate compose" in makefile
    assert "python3 -m pytest infra/tests" in makefile
    assert "$(MAKE) test-backend" in makefile


def test_rabbitmq_container_loads_definitions_on_boot() -> None:
    compose_text = COMPOSE.read_text()
    config_text = RABBITMQ_CONFIG.read_text()

    assert (
        "${COMPOSE_REPO_ROOT:-${PWD}}/infra/docker/rabbitmq/definitions.json:/etc/rabbitmq/definitions.json:ro"
        in compose_text
    )
    assert (
        "${COMPOSE_REPO_ROOT:-${PWD}}/infra/docker/rabbitmq/rabbitmq.conf:/etc/rabbitmq/conf.d/10-definitions.conf:ro"
        in compose_text
    )
    assert "management.load_definitions = /etc/rabbitmq/definitions.json" in config_text


def test_compose_resolves_repo_root_paths_from_supported_invocations() -> None:
    expected_root = str(ROOT)
    expected_mounts = {
        "/etc/rabbitmq/definitions.json": str(RABBITMQ_DEFINITIONS),
        "/etc/rabbitmq/conf.d/10-definitions.conf": str(RABBITMQ_CONFIG),
    }

    for with_project_directory in (False, True):
        config = _compose_config(with_project_directory=with_project_directory)
        services = config["services"]
        assert isinstance(services, dict)

        for service_name in (
            "auth-service",
            "booking-service",
            "contract-service",
            "dashboard-consumer",
            "document-service",
            "gateway",
        ):
            build = services[service_name]["build"]
            assert build["context"] == expected_root
            assert (ROOT / build["dockerfile"]).exists()

        rabbit_mounts = {
            volume["target"]: volume["source"]
            for volume in services["rabbitmq"]["volumes"]
            if volume["type"] == "bind"
        }
        assert rabbit_mounts == expected_mounts
        for source in rabbit_mounts.values():
            assert Path(source).exists()
