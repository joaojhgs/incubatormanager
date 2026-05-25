# SDL Phase 2 Review Notes

Updated: 2026-05-25

## Current status

The Phase 2 handoff scope has been reconciled into the integration branch. The operational backend services now expose domain endpoints beyond health checks, event consumers use `event_id` idempotency where events are consumed, and the targeted staff/client placeholder pages have been replaced by API-backed operational pages and ticket/client views.

## Backend/event-chain coverage

Covered in the current branch:

- Company create/update, detail, maturity, employees, stats, and event publishing paths.
- Contract list/detail/create, activate, terminate, expiration command, and lifecycle event publishing.
- Finance payment list/detail/company views, dashboard/report endpoints, monthly billing/overdue commands, and contract/booking event handlers.
- Space list/type/occupancy, contract projections, booking projections, and minimal contract-ended event handling.
- Booking public/internal/client flows and approve/reject/cancel/complete lifecycle events.
- Inventory equipment/type CRUD, assign/release flows, booking event projection endpoint, and client assignment scoping.
- Ticket create/list/my/detail/message flows with role and company scoping,
  plus a staff-only metrics endpoint for open-ticket dashboard counters.
- Dashboard overview/report aggregation against downstream services with guarded availability reporting and ticket metric snapshots.
- Document upload/list/download/delete paths backed by the configured document storage adapter.

## Frontend coverage

Covered in the current branch:

- Staff operational routes for contracts, finance, spaces, bookings, inventory, dashboard, and tickets no longer use placeholder sections.
- Client portal company, contract, payments, bookings, and tickets routes no longer use placeholder sections.
- User-facing strings added by the Phase 2 work are routed through the existing i18n dictionaries.

## Verification status

Local verification is the merge gate for this branch. The latest local evidence is recorded in `docs/AGENT_HANDOFF.md` and includes service checks/tests, frontend format/typecheck/lint/test/build, ruff, integration smoke checks, code review, and QA. Live Docker-dependent checks remain environment-gated when the Docker socket is unavailable.

## Remaining non-blocking hardening ideas

- Add richer domain-specific staff forms/detail pages as time allows.
- Expand browser e2e coverage once Docker access is available.
- Regenerate committed OpenAPI schema snapshots after any future endpoint or metadata changes.
