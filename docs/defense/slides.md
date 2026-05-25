# ILB Incubator Platform — Defense Deck

## Slide 1 — What was built

- A local, end-to-end platform for a business incubator.
- Staff portal for internal operations and client portal for incubated companies.
- Public booking request flow for unauthenticated space requests.
- Ten Django services behind one gateway, plus a Next.js 14 and Ant Design frontend.

Speaker notes:

- Open with the operational problem: managing companies, contracts, spaces, finance, bookings, inventory, support, and documents without mixing each domain into one database.
- State that the demo is local-first and designed for repeatable assessment.

## Slide 2 — Phase 2 scope

The implementation covers the planned Phase 2 service wave:

1. Auth and User
2. Company
3. Document
4. Contract
5. Finance
6. Space
7. Booking
8. Inventory
9. Ticket
10. Dashboard

Speaker notes:

- Emphasize that Inventory and Dashboard are included, not deferred.
- Mention that each service has its own Django application, models, migrations, tests, and Docker runtime.

## Slide 3 — Architecture boundaries

- Strict microservices in a monorepo.
- One PostgreSQL database per service.
- No shared ORM models or shared database schemas.
- Nginx gateway routes `/api/<service>/...` to internal service ports.
- Gateway-authenticated requests inject `X-User-Id`, `X-User-Role`, and `X-Company-Id` headers.

Speaker notes:

- The defense question to answer here is: “Where is service isolation proved?”
- Point to `docs/architecture.md`, the compose topology, and the per-service DB names.

## Slide 4 — Deployment topology

- Frontend is served through the gateway.
- Backend services are private to the Docker network.
- PostgreSQL, Redis, RabbitMQ, and MinIO provide local infrastructure.
- Scheduled work uses management commands in scheduler sidecars, not Celery.
- The stack is intended to be booted through `make demo` or compose/Tilt paths.

Speaker notes:

- Call out deliberate constraints: no Kubernetes, no cloud-only services, and no stack changes.
- Explain that unavailable Docker socket access is an environment blocker, not an architectural gap.

## Slide 5 — Event-driven workflows

RabbitMQ topic exchange: `incubator.events`.

Core event flows:

- `company.created` and `company.archived` update downstream read models.
- `contract.activated`, `contract.terminated`, and `contract.expired` drive finance, space, booking, and dashboard updates.
- `booking.approved`, `booking.cancelled`, `booking.rejected`, and `booking.completed` drive space, inventory, finance, and dashboard updates.
- `payment.recorded` refreshes dashboard and finance projections.

Speaker notes:

- Every event has `event_id`, `event_type`, `occurred_at`, and `payload`.
- Consumers are idempotent on `event_id`, so replaying or retrying the same event is safe.

## Slide 6 — Role-based product surfaces

Staff portal:

- Dashboard KPIs and operational summaries.
- Company, contract, finance, space, booking, inventory, ticket, and user management pages.

Client portal:

- Company profile, contract, payments, bookings, support tickets, and documents.

Public route:

- Booking request form for external users.

Speaker notes:

- Use the route split to show RBAC boundaries: staff, client, and public flows are visible in different route groups.
- Client-scoped requests must remain isolated by `X-Company-Id`.

## Slide 7 — Demo flow

Recommended live path:

1. Start the stack and seed representative demo data.
2. Login as Director.
3. Review dashboard service health and KPIs.
4. Open companies and inspect company status/maturity.
5. Activate or review a contract.
6. Inspect finance totals and payment states.
7. Approve or review bookings and observe inventory/space effects.
8. Open a ticket thread and show staff/client support separation.
9. Login as a client and verify only that client company's data is visible.
10. Submit or review a public booking request.

Speaker notes:

- Keep the demo focused on business flow rather than implementation minutiae.
- If live stack access fails, use this exact path as the backup recording storyboard.

## Slide 8 — Functional coverage map

| Area      | Evidence to show                         |
| --------- | ---------------------------------------- |
| Auth/User | Login, role routing, Director-only users |
| Company   | Company list/profile, maturity/status    |
| Document  | Upload/list/download integration points  |
| Contract  | Lifecycle and active contract data       |
| Finance   | Payments, overdue/pending/paid summaries |
| Space     | Occupancy and capacity views             |
| Booking   | Public/client/staff booking flows        |
| Inventory | Equipment status and booking assignment  |
| Ticket    | Staff and client ticket threads          |
| Dashboard | Aggregated operational metrics           |

Speaker notes:

- Keep this slide as the checklist for “did we cover the rubric-critical services?”
- Mention tests and local checks only after showing the user-visible behavior.

## Slide 9 — Quality and risk controls

- Local verification is the merge gate for this phase.
- Service checks include `manage.py check`, migration dry-runs, and targeted pytest suites.
- Frontend checks include typecheck, unit tests, lint, and production build.
- Integration smoke checks target client isolation, event idempotency, billing/overdue idempotency, inventory projections, ticket scoping, and dashboard authorization.
- Known live-demo risk: Docker socket access may block stack startup on restricted hosts.

Speaker notes:

- State the mitigation: maintain a deterministic demo script, seed data, and a backup recording path.
- Be transparent that local host access, not code structure, is the known blocker for live compose in restricted environments.

## Slide 10 — Roadmap and conclusion

Immediate hardening:

- Run `make demo` on a workstation with Docker socket access.
- Run gateway Playwright smoke tests against the live stack.
- Export a PDF from this deck and record the backup demo.

Future improvements:

- Expand dashboard charts and drill-through filters.
- Add more end-to-end Playwright coverage for cross-service event chains.
- Add operational metrics beyond health stubs.
- Improve performance measurements on seeded data.

Closing message:

- The project delivers the planned microservice platform with separated service ownership, event-driven integrations, role-aware portals, and a repeatable local defense path.
