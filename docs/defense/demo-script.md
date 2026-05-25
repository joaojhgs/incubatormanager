# Defense Demo Script

Use this script for the live defense and for the backup screen recording. Keep credentials in `.env` or locally supplied notes; do not commit passwords.

## 0. Preconditions

- Repository is checked out on the defense branch.
- `.env` exists and was generated from the project example values.
- Docker socket access is available for live stack startup.
- The seed step has representative records for users, companies, spaces, contracts, payments, bookings, inventory, tickets, dashboard data, and documents.

Recommended commands on a workstation with Docker access:

```bash
make demo
make seed
NODE_PATH="$PWD/frontend/node_modules" frontend/node_modules/.bin/playwright test -c e2e/playwright.config.ts
```

If Docker socket access is unavailable, state that the live compose path is host-blocked and use the backup recording path in section 5.

## 1. Opening narrative, 30 seconds

Say:

> This is a local business incubator management platform. It uses strict Django microservices with one database per service, a Next.js and Ant Design frontend, an Nginx gateway, and RabbitMQ events for cross-service consistency.

Show:

- `docs/architecture.md` service catalogue.
- Gateway path prefixes and per-service database names.

## 2. Staff demo path, 4 minutes

### 2.1 Login and dashboard

1. Open the frontend through the gateway.
2. Login as a Director or Staff user.
3. Land on the staff dashboard.
4. Point out KPI cards: companies, contracts, pending bookings, open tickets, and finance summary.

What to explain:

- Dashboard data is an aggregate read surface.
- Protected backend requests rely on gateway-injected identity headers.

### 2.2 Company and contract operations

1. Navigate to Companies.
2. Open or identify an incubated company.
3. Show status/maturity information.
4. Navigate to Contracts.
5. Show active/draft/terminated contract state where seed data allows.

What to explain:

- Company remains the source of truth for company identity and lifecycle.
- Contract state changes can publish events for finance, space, booking, and dashboard consumers.

### 2.3 Finance and billing

1. Navigate to Finance.
2. Show total, paid, pending, and overdue amounts.
3. Explain monthly billing and overdue processing as management-command scheduled work.

What to explain:

- Scheduled work is intentionally implemented without Celery.
- Payment changes publish `payment.recorded` for downstream aggregate refresh.

### 2.4 Space, booking, and inventory

1. Navigate to Spaces and show capacity or occupancy data.
2. Navigate to Bookings.
3. Show pending/approved/completed bookings.
4. If available, approve a pending booking.
5. Navigate to Inventory and show equipment state.

What to explain:

- Booking lifecycle events update space and inventory projections.
- Consumers dedupe by `event_id` so retries are safe.

### 2.5 Tickets and documents

1. Navigate to Tickets.
2. Open a ticket or show list status values.
3. Show document list/upload integration where the seeded route supports it.

What to explain:

- Ticket access is role- and company-aware.
- Document metadata lives in the document service; file objects use MinIO.

## 3. Client demo path, 2 minutes

1. Logout from staff.
2. Login as a Client user.
3. Open the client portal landing page.
4. Show company, contract, payments, bookings, tickets, and documents where records exist.
5. Confirm that records belong only to the client user's company.

What to explain:

- `X-Company-Id` is the isolation boundary for client views.
- Client routes are intentionally separate from staff route groups.

## 4. Public booking request, 1 minute

1. Open `/booking-request` without an authenticated session.
2. Submit or review the public booking flow.
3. Return to staff bookings to show operational follow-up if the environment allows it.

What to explain:

- The public path is the entry point for external requests.
- Staff approval is the controlled transition into operational booking state.

## 5. Backup recording path

Record a 3-minute screen capture with this storyboard:

1. Title card: project name and architecture summary.
2. Staff dashboard with KPI cards.
3. Company and contract lists.
4. Finance summary.
5. Booking list and status action.
6. Inventory state.
7. Ticket list/thread.
8. Client portal isolation view.
9. Public booking request.
10. Closing slide with verification evidence and known Docker-host requirement.

Recommended recording checklist:

- Browser zoom at 100% or 110%.
- Terminal font large enough to read command output.
- Avoid showing `.env` contents or passwords.
- Narrate one sentence per screen: what this proves and which service boundary it touches.
- Store the recording outside git unless a small approved file is intentionally added.

## 6. Questions to be ready for

| Question                                      | Short answer                                                                                                                            |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| How is microservice isolation enforced?       | One Django app and one PostgreSQL database per bounded context; services integrate through REST and RabbitMQ events, not shared tables. |
| How is client data isolated?                  | Gateway verification injects `X-Company-Id`; downstream services scope client routes by that company id.                                |
| Why no Celery?                                | The project constraint is no Celery; scheduled work uses Django management commands in scheduler sidecars.                              |
| What makes events safe to retry?              | Every event carries `event_id`; consumers persist processed IDs and skip duplicate handling.                                            |
| What if the live demo host cannot use Docker? | Use the backup recording path and state the host Docker socket blocker transparently.                                                   |
