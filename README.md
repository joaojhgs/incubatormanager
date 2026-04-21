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
├── eslint.config.mjs  # ESLint (flat config) for JS tooling at the repo root
├── package.json       # root devDependencies: eslint + prettier
├── pyproject.toml     # Ruff configuration for Python services and libs
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

## Linting and formatting

Install Python 3.12 and Node 20, then install dev tooling:

```bash
python -m pip install pre-commit ruff
```

If your Python is externally managed (PEP 668 on many Linux distros), install
`pre-commit` and `ruff` inside a virtual environment or with `pipx` instead of
using `pip` globally.

```bash
npm ci
npm --prefix frontend ci
pre-commit install
```

Run the same checks as CI locally:

```bash
pre-commit run --all-files
make lint
```

Ruff reads `pyproject.toml`. ESLint uses the root flat config for repo-level
JavaScript (`eslint.config.mjs`) and the Next.js app lint script under
`frontend/` (`.eslintrc.json`). Prettier reads `.prettierrc.json` at the root
and `frontend/.prettierrc` for app sources.
