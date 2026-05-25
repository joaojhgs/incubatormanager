# Project Handoff — ILB Incubator Platform

**Updated:** 2026-05-25  
**Project:** sdl-project-group-20  
**Phase:** Phase 2 implementation and local hardening

## Current implementation status

The repository now contains the Phase 2 service wave needed for the local demo path:

- Auth, Company, Document, Contract, Finance, Space, Booking, Inventory, Ticket, and Dashboard services are present under `services/`.
- Service boundaries remain independent: each Django service owns its models and migrations; cross-service references are UUID projections.
- Gateway-injected identity headers (`X-User-Id`, `X-User-Role`, `X-Company-Id`) are the authorization source for downstream services.
- RabbitMQ event envelopes use `event_id`, `event_type`, `occurred_at`, and `payload`; consumers persist processed `event_id` rows for idempotency.
- Frontend placeholder pages for staff/client operational areas have been replaced with connected health/data panels and ticket/client views.

## Important constraints

- Do not change the technology stack.
- Keep a separate database per service.
- Do not introduce Celery, Kubernetes, or cloud services.
- Keep client data isolated by `X-Company-Id`.
- Route user-facing frontend strings through the existing i18n dictionaries.
- Keep commit and MR text project-authored; do not include external-tool attribution.

## Local verification policy

GitLab shared runners are not the merge gate for this work. Use local checks:

1. Service-level `manage.py check`.
2. `makemigrations --check --dry-run` after model changes.
3. Targeted pytest suites per touched service.
4. Frontend `typecheck`, tests, lint, and build.
5. Integration smoke checks and `make demo` before final handoff.

## Priority areas already addressed in this wave

- Company write/update, maturity, employee, stats, and event publishing paths.
- Contract lifecycle: draft, activation, termination, expiration, monthly fee snapshot, and events.
- Finance payments, billing/overdue commands, event handlers, dashboard/report endpoints, and payment-recorded event.
- Space occupancy and contract/booking projections.
- Booking public/internal/client flows and lifecycle events.
- Inventory equipment CRUD, assignment/release flows, and booking event handlers.
- Ticket RBAC-scoped ticket/thread endpoints.
- Dashboard service health/metric aggregation endpoints.
- Frontend placeholder replacement for staff and client operational pages.

## Latest local verification evidence

The integrated Phase 2 tree was verified locally on 2026-05-25 with:

- `manage.py check`, migration dry-runs, and full pytest suites for auth, company, document, contract, finance, space, booking, inventory, ticket, and dashboard services.
- Frontend `typecheck`, unit tests, lint, and production build.
- Targeted integration smoke tests covering client isolation, contract and booking event publication, event consumer idempotency, finance billing/overdue idempotency, inventory assignment/release projections, ticket scoping, and dashboard authorization.
- Playwright gateway-auth probe attempted against `127.0.0.1:80`; it failed because the live Docker stack was unavailable in the local environment.
- `make demo` attempted; it failed before stack startup because the current user could not access `/var/run/docker.sock`.

## Recommended next checks

On a workstation with Docker socket access, run:

```bash
make demo
make seed
NODE_PATH="$PWD/frontend/node_modules" frontend/node_modules/.bin/playwright test -c e2e/playwright.config.ts
```

If additional changes land, also rerun the relevant service tests plus frontend `typecheck`, tests, lint, and build.
