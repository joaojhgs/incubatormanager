# ILB Incubator Management Platform

Monorepo for the ILB (Incubadora de Lanheses e Bertiandos) Incubator Management
Platform. A microservices system for managing incubated companies, contracts,
finance, workspaces, bookings, inventory, tickets, and documents.

## Stack

- **Backend:** Django 5 + DRF, one service per bounded context, Postgres per
  service.
- **Events:** RabbitMQ topic exchange `incubator.events`.
- **Gateway:** Nginx with `auth_request` JWT validation (15 min access / 7 day
  refresh) against `auth-service`.
- **Storage:** MinIO (S3-compatible) for uploaded documents.
- **Frontend:** Next.js 14 App Router + TypeScript + Ant Design v5, i18n pt-PT
  default.
- **Scheduler:** sidecar containers running host cron (no Celery).
- **Local dev:** Tilt + docker compose (`tilt up`).
- **Timezone:** `Europe/Lisbon`.

## Repository layout

```
repo-root/
├── services/            # one Django service per bounded context
├── gateway/             # Nginx reverse proxy + JWT auth_request
├── frontend/            # Next.js 14 App Router (Ant Design v5)
├── libs/py-common/      # shared event bus, auth headers, bootstrap helpers
├── infra/
│   ├── docker/          # base Dockerfile templates
│   ├── cron/            # host-cron files mounted into scheduler sidecars
│   └── seed/            # fixture data (10-of-everything)
├── .github/workflows/   # CI pipelines (kept in sync with GitLab CI)
├── docs/                # architecture, deploy, defense artefacts
├── Makefile             # top-level developer targets
├── .python-version      # 3.12
├── .nvmrc               # 20
└── README.md
```

Full architecture and rationale: `docs/`.

## Quick start

Prerequisites: Docker Engine + Compose v2, Tilt, Python 3.12 (`.python-version`),
Node 20 (`.nvmrc`).

```bash
# Run the full stack (once compose is wired up)
make up

# Hot-reload development
tilt up

# List all Makefile targets
make help
```

## Contributing

- Branches: `w<week>/<slug>` (e.g. `w1/init-monorepo`).
- Commits: Conventional Commits (`<type>(<scope>): <subject>`, imperative,
  ≤72 chars).
- One merge request per task, squash-merge.
- English-only code and commit messages; pt-PT in UI copy.
