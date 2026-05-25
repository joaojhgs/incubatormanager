# Defense Checklist

## Before the defense

- [ ] Confirm the branch contains the latest integrated Phase 2 changes.
- [ ] Generate or verify local `.env` without committing secrets.
- [ ] Confirm Docker socket access on the demo machine.
- [ ] Review `docs/user.md` for the staff, client, and public booking walkthrough.
- [ ] Run `make demo` on a machine with Docker access.
- [ ] Run `make seed` after stack startup.
- [ ] Run the gateway Playwright smoke command if the live stack is available.
- [ ] Update `docs/defense/local-qa-evidence.md` with the latest pass/fail commands and blockers.
- [ ] Update `docs/defense/release-evidence.md` before defense sign-off.
- [ ] Export `docs/defense/slides.md` to PDF if a PDF is required by the defense format.
- [ ] Record a 3-minute backup demo if live compose remains environment-sensitive.
- [ ] Keep demo credentials in private notes, not in repository files.

## Live demo health checks

- [ ] Frontend loads through the gateway.
- [ ] Staff login succeeds.
- [ ] Client login succeeds.
- [ ] Dashboard shows data rather than blank panels.
- [ ] Company page shows seeded companies.
- [ ] Contract page shows seeded contracts.
- [ ] Finance page shows paid, pending, and overdue values.
- [ ] Spaces page shows capacity or occupancy data.
- [ ] Bookings page shows at least one booking and status.
- [ ] Inventory page shows seeded equipment.
- [ ] Tickets page shows support requests.
- [ ] Client portal shows only the logged-in client's company data.
- [ ] Public booking request page loads without authentication.

## Architecture points to cover

- [ ] Strict microservices in a monorepo.
- [ ] One PostgreSQL database per service.
- [ ] Nginx gateway as the only public API entry point.
- [ ] Gateway-injected identity headers for downstream RBAC.
- [ ] RabbitMQ `incubator.events` topic exchange.
- [ ] Event envelope fields: `event_id`, `event_type`, `occurred_at`, `payload`.
- [ ] Consumer idempotency by `event_id`.
- [ ] MinIO-backed document storage.
- [ ] Management-command schedulers instead of Celery.
- [ ] Local verification gates as the phase merge criteria.

## Functional coverage to demonstrate

- [ ] Auth/User: login and role-aware routing.
- [ ] Company: list/profile/maturity or status data.
- [ ] Document: upload/list/download integration point.
- [ ] Contract: lifecycle status and company linkage.
- [ ] Finance: payments and summary values.
- [ ] Space: occupancy/capacity view.
- [ ] Booking: public, client, or staff booking flow.
- [ ] Inventory: equipment records and assignment status.
- [ ] Ticket: ticket list/thread and staff/client access.
- [ ] Dashboard: operational aggregate overview.

## If the live stack fails

- [ ] Capture the exact failing command and short error.
- [ ] State whether the failure is host/environment access, service startup, or application behavior.
- [ ] Use the backup recording storyboard from `docs/defense/demo-script.md`.
- [ ] Still show code evidence for architecture and service boundaries.
- [ ] Do not expose secrets while troubleshooting.

## Final repository hygiene

- [ ] No passwords, tokens, or `.env` contents are committed.
- [ ] Defense docs do not include external-tool attribution.
- [ ] Defense docs reference project files and local verification commands.
- [ ] Any generated PDF/video artifact is intentionally included or intentionally kept outside git.
