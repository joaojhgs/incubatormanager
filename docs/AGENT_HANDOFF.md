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

## Recommended next checks

Run these from the repository root after pulling any new local changes:

```bash
for svc in company contract finance space booking inventory ticket dashboard; do
  (cd services/$svc-service && PYTHONPATH=../../libs/py-common python3 manage.py check)
done

npm --prefix frontend run typecheck
npm --prefix frontend run test
npm --prefix frontend run lint
npm --prefix frontend run build
```

Then run integration smoke checks and `make demo`.
