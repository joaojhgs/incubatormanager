# Local QA Evidence and Demo Gate

This file records the local QA gate for the defense/demo handoff. Use it with
`docs/defense/demo-script.md` and `docs/defense/checklist.md` when preparing the
live walkthrough.

## Browser smoke coverage

Targeted Playwright smoke coverage lives in
`frontend/tests/e2e/qa-hardening-smoke.spec.ts` and exercises the non-Docker
fallback path:

- Staff dashboard renders mocked gateway data from company, contract, booking,
  ticket, and finance endpoints.
- Client portal requests company-scoped contract and payment URLs using the
  authenticated `company_id` claim.
- Staff inventory correlates spaces, booking records, and equipment assignments.
- Public booking request remains unauthenticated and validates required fields.

Run it with:

```bash
cd frontend
npx playwright test tests/e2e/qa-hardening-smoke.spec.ts
```

## Local gate commands

When Docker socket access is available, run the compose-backed gate:

```bash
make local-gate
```

When Docker socket access is unavailable, run the host-only gate. It exercises lint, formatting, frontend typecheck/tests/build, cron validation, shared libraries, and each Django service pytest/migration check without starting containers:

```bash
make local-gate-host
```

Equivalent expanded commands for CI logs and troubleshooting:

```bash
ruff check .
npm run lint
npm run format:check
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
python3 -m py_compile infra/scripts/cron-runner.py
python3 infra/scripts/cron-runner.py --dry-run infra/cron/booking.crontab
python3 infra/scripts/cron-runner.py --dry-run infra/cron/contract.crontab
python3 infra/scripts/cron-runner.py --dry-run infra/cron/finance.crontab
python3 -m pytest infra/tests -q
python3 -m pip install -q -e "libs/py-common[dev]"
cd libs/py-common && python3 -m pytest -q
# Or, without Docker, loop each services/*-service directory:
# python3 manage.py makemigrations --check --dry-run && python3 -m pytest -q
```

## Release gate status (host-only)

Current status: PASS on 2026-05-25.

`make local-gate-host` completed successfully with:

- `ruff check .` PASS.
- `npm run lint` PASS.
- `npm run format:check` PASS.
- `npm --prefix frontend run typecheck` PASS.
- `npm --prefix frontend test` PASS: 19 files and 58 tests.
- `npm --prefix frontend run build` PASS: 26 app routes generated.
- Cron parser dry runs PASS.
- `python3 -m pytest infra/tests` PASS: 15 tests.
- `libs/py-common` pytest PASS: 50 tests.
- Backend service migration checks and pytest PASS:
  - auth-service: 84 tests.
  - company-service: 62 tests.
  - contract-service: 10 tests.
  - finance-service: 20 tests.
  - space-service: 7 tests.
  - booking-service: 20 tests.
  - inventory-service: 7 tests.
  - ticket-service: 14 tests.
  - dashboard-service: 10 tests.
  - document-service: 49 tests.

## Browser e2e status

Current status: PASS for the frontend mocked browser suite on 2026-05-25.

`npm --prefix frontend run test:e2e` completed successfully with 11 Playwright
tests, covering login, client portal scoping, staff dashboard aggregates, staff
inventory correlation, public booking validation, and user-management flows.

## Compose/gateway status

Current status: blocked by environment on this host.

- `make demo` stops before application startup because the current user cannot
  connect to `/var/run/docker.sock`.
- `npm run test:e2e` for the root gateway suite fails with
  `ECONNREFUSED 127.0.0.1:80` because the compose gateway is not running.

These are environment blockers for Docker-backed evidence. Rerun `make demo`,
`make local-gate`, and the root gateway Playwright suite on a workstation where
the current user can access the Docker socket.

## Docker-dependent demo blocker

The live `make demo` path requires Docker socket access. In this container,
Docker-dependent commands are host-blocked before application startup:

```text
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

When this blocker appears, use the backup walkthrough in
`docs/defense/demo-script.md` and rerun `make demo` on a workstation where the
current user can access `/var/run/docker.sock`.
