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
- Public booking request page remains unauthenticated and validates required
  fields.

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
docker compose --env-file .env.example --project-directory . -f infra/docker-compose.yml config --quiet
# Or, without Docker, loop each services/*-service directory:
# python3 manage.py makemigrations --check --dry-run && python3 -m pytest -q
```

## Docker-dependent demo blocker

The live `make demo` path requires Docker socket access. In this worker
container, Docker-dependent commands are host-blocked before application
startup:

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

When this blocker appears, use the backup walkthrough in
`docs/defense/demo-script.md` and rerun `make demo` on a workstation where the
current user can access `/var/run/docker.sock`.
