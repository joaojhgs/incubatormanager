# User Guide

This guide describes the browser workflows available in the ILB Incubator Platform for staff, client users, and unauthenticated public booking requesters. It is intended for demos, acceptance checks, and first-line support.

## Access and sessions

- Open the application through the gateway URL used by the deployment, for example `http://localhost/` in the local compose stack or `http://localhost:3000/` when running the frontend development server directly.
- Sign in at `/login` with an account created by the auth service or by the local seed data.
- Staff roles are redirected to the internal dashboard. Client roles are redirected to the client portal.
- Protected routes redirect unauthenticated users back to `/login` with the original destination preserved.
- The public booking request route is intentionally available without signing in.

## Staff portal

Staff users manage incubator operations from the internal navigation.

### Dashboard

Use `/dashboard` as the operational overview:

- Review company, contract, pending booking, open ticket, and finance summary cards.
- Follow drill-through links to the relevant operational page when a card indicates pending work.
- Treat empty or unavailable panels as a sign to check the downstream service health and seed data.

### Companies and users

Use the Companies and Users pages to manage incubated company identity and platform access:

- `/companies` lists companies and exposes the detail path for a selected company.
- `/companies/new` creates a company record.
- `/companies/[id]` shows company profile, maturity/status information, employees, and linked documents when records exist.
- `/users` lists platform users.
- `/users/new` creates a user account and links client users to their company where applicable.

### Contracts and finance

Use Contracts and Finance to review commercial state:

- `/contracts` lists contract status, company/space linkage, area, rate, and lifecycle dates.
- `/finance` shows total, paid, pending, and overdue amounts, plus payment rows and due dates.
- Follow overdue and pending payment indicators before the demo so unresolved data can be explained as seeded business state, not application failure.

### Spaces, bookings, and inventory

Use these pages to manage operational capacity:

- `/spaces` shows physical space capacity and occupancy information.
- `/bookings` lists booking requests and supports staff lifecycle actions where enabled by the backend state.
- `/inventory` shows equipment, status, assignment history, and booking/space projection information.
- When approving or completing bookings, verify that linked inventory and space projections still match the expected operational state.

### Tickets

Use `/tickets` to manage support requests:

- Staff can review ticket status and client-originated issues.
- Ticket counters feed dashboard open-ticket metrics.
- Use ticket state during demos to show client/staff separation and operational follow-up.

## Client portal

Client users access company-scoped data under `/portal`.

- `/portal` summarizes the client user's company, contract, next payment, recent payments, bookings, and support state.
- `/portal/company` shows the company profile attached to the authenticated client's `company_id`.
- `/portal/contract` shows the active or recent contract records for that company.
- `/portal/payments` lists company-scoped payments.
- `/portal/bookings` lists the client's bookings and exposes booking submission where available.
- `/portal/tickets` lets clients open and follow support requests.

Client data isolation depends on the authenticated `company_id` claim. If a client account has no company association, the portal should show the no-company support message rather than another company's data.

## Public booking request

Use `/booking-request` for unauthenticated booking enquiries:

1. Open the route without logging in.
2. Enter requester name, email, phone, requested time, and supporting notes.
3. Submit the request for staff review.
4. During demos, return to the staff booking page only if the local stack and seed data support the follow-up state.

## Expected runtime behavior by role

| Role              | Entry route        | Expected access                                                                                 | Isolation check                                                                             |
| ----------------- | ------------------ | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Staff or Director | `/dashboard`       | Staff dashboard, companies, contracts, finance, spaces, bookings, inventory, tickets, and users | Staff pages should not expose client-only portal navigation as the primary workflow.        |
| Client            | `/portal`          | Company-scoped company, contract, payments, bookings, and tickets                               | Requests must use the authenticated company id and must not show another company’s records. |
| Public requester  | `/booking-request` | Booking enquiry form without a signed-in session                                                | The route must not require a refresh token or access token.                                 |

## Release / defense evidence checklist

Before using this guide as release or defense evidence, confirm:

- `docs/defense/release-evidence.md` contains the latest command results and blocker status.
- `docs/defense/local-qa-evidence.md` records any host-only or Docker-specific limitations.
- Frontend typecheck/build blockers are fixed before browser e2e output is reported as passing.
- Docker-backed demo evidence was collected on a machine with Docker socket access, or the backup recording path was used explicitly.

## Post-release smoke verification

After a release candidate or defense branch is prepared, run the following smoke path on the target demo machine:

```bash
make demo
make seed
NODE_PATH="$PWD/frontend/node_modules" frontend/node_modules/.bin/playwright test -c e2e/playwright.config.ts
make down
make ps
```

Expected result: the stack starts, seed data loads, gateway/auth smoke passes, shutdown completes, and `make ps` shows no unexpected running project containers after teardown. If Docker access is unavailable, record that as an environment blocker rather than a product pass.

## Demo readiness checklist for operators

Before a live walkthrough:

1. Confirm `.env` exists locally and does not contain committed secrets.
2. Start and seed the local stack on a machine with Docker socket access:
   ```bash
   make demo
   make seed
   ```
3. Run the gateway Playwright smoke when the stack is up:
   ```bash
   NODE_PATH="$PWD/frontend/node_modules" frontend/node_modules/.bin/playwright test -c e2e/playwright.config.ts
   ```
4. If Docker is unavailable, use the backup recording flow in `docs/defense/demo-script.md` and keep the blocker text in `docs/defense/local-qa-evidence.md` current.
5. Keep demo credentials in private notes or local environment files, never in repository documentation.

## Troubleshooting

| Symptom                                       | Likely cause                                                   | Operator action                                                                             |
| --------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Login returns to `/login`                     | Missing/expired session or wrong role for route                | Sign in again with the appropriate staff or client account.                                 |
| Client portal shows no company association    | Client user lacks `company_id`                                 | Link the user to a company in seed/admin data before the demo.                              |
| Dashboard panels are empty                    | Seed data is missing or downstream service returned no records | Run `make seed` and inspect the relevant service logs.                                      |
| Compose/demo command cannot connect to Docker | Host user lacks Docker socket access                           | Move to a workstation with Docker access or use the backup recording path.                  |
| Browser smoke fails before tests run          | Frontend build/typecheck failed                                | Fix the reported TypeScript/build error before treating the e2e result as product evidence. |
