# ILB Incubator Management Platform

Monorepo for the ILB (Incubadora de Lanheses e Bertiandos) Incubator Management
Platform. The project is a Docker Compose-first microservices system for managing
incubated companies, contracts, finance, workspaces, bookings, inventory,
tickets, documents, and role-specific browser workflows.

## Current scope

The Phase 2 implementation contains the local demo path described in
`docs/AGENT_HANDOFF.md` and `docs/sdl-phase2-review-notes.md`:

- Ten Django services are present under `services/`: auth, company, contract,
  finance, space, booking, inventory, ticket, dashboard, and document.
- Each service owns its database schema and exposes REST endpoints through the
  gateway; cross-service references are UUID projections rather than shared ORM
  models.
- Gateway-injected identity headers (`X-User-Id`, `X-User-Role`,
  `X-Company-Id`) drive downstream authorization and client data isolation.
- RabbitMQ events use a shared envelope (`event_id`, `event_type`,
  `occurred_at`, `payload`) and consumers persist processed event IDs for
  idempotency.
- The frontend includes connected staff pages, a client portal, and an
  unauthenticated public booking request route.

## Stack

- **Backend:** Django 5 + Django REST Framework, one deployable service per
  bounded context, PostgreSQL database per service.
- **Gateway:** Nginx with `auth_request` JWT validation against `auth-service`;
  trusted user headers are forwarded to upstream services.
- **Events:** RabbitMQ topic exchange `incubator.events` with durable messages.
- **Storage:** MinIO (S3-compatible) for uploaded documents.
- **Frontend:** Next.js 14 App Router + TypeScript + Ant Design v5, React Query,
  i18n dictionaries, and `pt-PT` defaults.
- **Scheduler:** service sidecar containers running host-style cron entries from
  `infra/cron/`; Celery is intentionally not used.
- **Local dev:** Tilt + Docker Compose (`tilt up`) or Make targets.
- **Timezone:** `Europe/Lisbon`.

## Repository layout

```text
repo-root/
├── services/              # Django services, one bounded context per directory
├── gateway/               # Nginx reverse proxy and auth_request configuration
├── frontend/              # Next.js 14 App Router application
├── libs/py-common/        # shared event bus, auth header, and bootstrap helpers
├── infra/
│   ├── cron/              # scheduler sidecar crontabs
│   ├── docker-compose*.yml# compose topology and development overrides
│   ├── scripts/           # cron runner and storage initialization helpers
│   └── seed/              # deterministic local demo seed entrypoint
├── docs/                  # architecture, deployment, user, event, defense docs
├── e2e/                   # gateway/browser smoke tests
├── Makefile               # top-level developer and verification targets
├── package.json           # root JS lint/format/e2e tooling
├── pyproject.toml         # Ruff configuration for Python services and libs
├── .gitlab-ci.yml         # GitLab CI entrypoint
├── .python-version        # Python 3.12
├── .nvmrc                 # Node 20
└── README.md
```

Full architecture and rationale: `docs/architecture.md`. Event payloads:
`docs/events.md`. Operators: `docs/deploy.md`. Branch naming, commits, and MRs:
`docs/contributing.md`. Browser workflows: `docs/user.md`.

## Quick start

Prerequisites: Docker Engine + Compose v2, Tilt (optional, for live reload),
Python 3.12 (`.python-version`), Node 20 (`.nvmrc`).

From a fresh clone:

```bash
git clone https://gitlab.coding.ipb.pt/sdl/2025-2026/projects/sdl-project-group-20.git
cd sdl-project-group-20
cp .env.example .env
```

Edit `.env` for your machine at minimum: `POSTGRES_PASSWORD`,
`DJANGO_SECRET_KEY`, per-service `*_DB_PASSWORD` values, MinIO credentials, and
`NEXT_PUBLIC_API_URL` if the browser should call a gateway origin other than
`http://localhost`.

Run the full stack in the background:

```bash
make up
```

Wait until containers report healthy (`make ps`), then open `http://localhost/`.
The API is under `http://localhost/api/...`. Quick smoke checks:

```bash
curl -fsS http://localhost/health
curl -fsS http://localhost/api/auth/health
```

Hot-reload development (bind mounts + Tilt):

```bash
tilt up
```

Other targets: `make help`.

## Verification

Local verification is the merge gate for this branch. For a full host-side gate
where dependencies are installed, run:

```bash
make local-gate-host
```

Useful focused checks:

```bash
ruff check .
npm run lint
npm run format:check
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
python3 -m pytest infra/tests
make test-libs
make test-backend-host
```

Docker-backed demo and browser smoke checks require access to the Docker socket:

```bash
make demo
make seed
NODE_PATH="$PWD/frontend/node_modules" frontend/node_modules/.bin/playwright test -c e2e/playwright.config.ts
```

Record environment blockers, such as missing Docker socket access, separately
from product failures. Current release and defense evidence is maintained in
`docs/defense/release-evidence.md` and `docs/defense/local-qa-evidence.md`.

## CI/CD and production deployment

GitLab CI validates compose configuration, runs path-filtered backend/frontend
checks, detects changed deployable services, builds only those images, pushes
them to the GitLab container registry, and deploys `main` automatically to the
production Docker host using SSH and Docker Compose.

Production deployment is configured with protected GitLab variables instead of
committed secrets. The course VM user is fixed as `a69603`; configure
`DEPLOY_HOST`, `DEPLOY_PASSWORD`, and either `DEPLOY_ENV_FILE_BASE64` or
`DEPLOY_ENV_FILE`. See `docs/deploy.md` for the full rollout flow and host
prerequisites.

## Contributing

See `docs/contributing.md` for branch naming, Conventional Commits, MR hygiene,
and review expectations.

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

Run the same style checks used by local verification:

```bash
pre-commit run --all-files
make lint
```

Ruff reads `pyproject.toml`. ESLint uses the root flat config for repo-level
JavaScript (`eslint.config.mjs`) and the Next.js app lint script under
`frontend/` (`.eslintrc.json`). Prettier reads `.prettierrc.json` at the root
and `frontend/.prettierrc` for app sources.
