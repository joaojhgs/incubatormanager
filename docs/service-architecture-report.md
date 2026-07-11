# Service Architecture, Sidecars, RabbitMQ, and Known Spec Deviations

Date: 2026-06-02

This report documents the current runtime architecture of the ILB Incubator
platform as implemented in this repository. It focuses on service boundaries,
sidecar containers, RabbitMQ integration, schedulers, data storage, and the
items from the original plan that were intentionally implemented differently or
left as known deviations.

The report is based on the current source tree, especially:

- `infra/docker-compose.yml`
- `infra/docker-compose.production.yml`
- `infra/cron/*.crontab`
- `infra/scripts/cron-runner.py`
- `libs/py-common/ilb_common/event_bus.py`
- `gateway/nginx.conf`
- service management commands and event handlers under `services/*/core/`
- `docs/events.md`
- `/home/developer/docs2/phase2-implementation-plan.md`

## 1. High-level architecture

The project is a Docker Compose based microservice platform. Each business
bounded context is implemented as a separate Django REST Framework service. A
Next.js frontend is served behind an Nginx gateway, and all browser/API traffic
is routed through that gateway.

Runtime infrastructure:

| Component     | Role                                                                                                                                                             |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nginx gateway | Public HTTP entry point on port 80 in deployed runs. Routes `/api/...` to backend services and `/` to the frontend. Performs JWT validation with `auth_request`. |
| Frontend      | Next.js 14 application for staff, client, and public flows.                                                                                                      |
| PostgreSQL 16 | One shared PostgreSQL container with one logical database and one database user per service.                                                                     |
| Redis         | Available as shared infrastructure. Currently used directly by `auth-service` for refresh-token blacklist and login/rate-limit cache when `REDIS_URL` is set.    |
| RabbitMQ      | Topic exchange `incubator.events` for asynchronous integration events.                                                                                           |
| MinIO         | S3-compatible document object storage used by `document-service`.                                                                                                |

The backend services are not published directly to the host. They listen on
internal Docker-network ports from 8001 to 8010 and are exposed externally only
through the gateway path prefixes.

## 2. Service catalogue

| Service             | Port | Database       | Main responsibility                                                                                          |
| ------------------- | ---: | -------------- | ------------------------------------------------------------------------------------------------------------ |
| `auth-service`      | 8001 | `auth_db`      | Users, JWT login, refresh/logout, token validation, role/company claims, login throttling.                   |
| `company-service`   | 8002 | `company_db`   | Companies, CAE, maturity stages, company profile data, employee/workforce records, company stats.            |
| `contract-service`  | 8003 | `contract_db`  | Contracts between companies and spaces, activation, termination, expiration, contract events.                |
| `finance-service`   | 8004 | `finance_db`   | Billing contracts, payments, rental charges, finance dashboard/report endpoints, overdue handling.           |
| `space-service`     | 8005 | `space_db`     | Space types, spaces, space prices/capacity/status, occupancy map, space projections from contracts/bookings. |
| `booking-service`   | 8006 | `booking_db`   | Authenticated and public booking requests, booking lifecycle, booking calendar/availability, booking events. |
| `inventory-service` | 8007 | `inventory_db` | Equipment types, equipment, assignment history, equipment projections from booking events.                   |
| `ticket-service`    | 8008 | `ticket_db`    | Client support tickets, staff queue, messages, ticket status, ticket metrics.                                |
| `dashboard-service` | 8009 | `dashboard_db` | Staff dashboard read models, service health snapshots, dashboard aggregate endpoints.                        |
| `document-service`  | 8010 | `document_db`  | Document metadata and MinIO-backed uploads/downloads.                                                        |

### 2.1 Database separation

The implementation uses one PostgreSQL container, but it initializes separate
logical databases and users:

- `auth_db` owned by `auth_svc`
- `company_db` owned by `company_svc`
- `contract_db` owned by `contract_svc`
- `finance_db` owned by `finance_svc`
- `space_db` owned by `space_svc`
- `booking_db` owned by `booking_svc`
- `inventory_db` owned by `inventory_svc`
- `ticket_db` owned by `ticket_svc`
- `dashboard_db` owned by `dashboard_svc`
- `document_db` owned by `document_svc`

This meets the project requirement of separate persistence per service at the
logical database/schema ownership level while keeping local and VM deployment
simple.

## 3. Gateway and authentication flow

The Nginx gateway is the only public HTTP API entry point. The route table in
`gateway/nginx.conf` maps each prefix to the corresponding upstream service.
Examples:

| Public path       | Upstream                 |
| ----------------- | ------------------------ |
| `/api/auth/`      | `auth-service:8001`      |
| `/api/companies/` | `company-service:8002`   |
| `/api/contracts/` | `contract-service:8003`  |
| `/api/finance/`   | `finance-service:8004`   |
| `/api/spaces/`    | `space-service:8005`     |
| `/api/bookings/`  | `booking-service:8006`   |
| `/api/inventory/` | `inventory-service:8007` |
| `/api/tickets/`   | `ticket-service:8008`    |
| `/api/dashboard/` | `dashboard-service:8009` |
| `/api/documents/` | `document-service:8010`  |

Most protected routes run through `auth_request /auth/verify`. The gateway sends
the JWT to `auth-service`, then forwards trusted identity headers to downstream
services:

- `X-User-Id`
- `X-User-Role`
- `X-Company-Id`

Downstream services use the shared header authentication from `libs/py-common`
to apply role-based access control and client company scoping. Public routes,
such as selected booking and public space/equipment endpoints, bypass JWT
verification by explicit gateway locations.

The gateway also has a small Nginx auth cache for `auth_request` responses. This
is separate from the Redis dashboard-caching question discussed later.

## 4. Sidecars

In this project, a sidecar is a Compose service that uses the same image and
codebase as a main service but runs a different command. Sidecars keep
background work outside the request/response web process without introducing
Celery, Kubernetes, or additional workers beyond Docker Compose.

### 4.1 Consumer sidecars

Consumer sidecars are long-running Django management commands that subscribe to
RabbitMQ and update local read models or projections.

| Sidecar              | Image/codebase      | Command                                     | Purpose                                                                                                |
| -------------------- | ------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `finance-consumer`   | `finance-service`   | `python manage.py consume_finance_events`   | Consumes contract and booking events, maintains finance billing/payment state.                         |
| `space-consumer`     | `space-service`     | `python manage.py consume_space_events`     | Consumes contract and booking events, updates space contract/booking projections and derived statuses. |
| `inventory-consumer` | `inventory-service` | `python manage.py consume_inventory_events` | Consumes booking events, marks equipment in use or released.                                           |
| `dashboard-consumer` | `dashboard-service` | `python manage.py consume_dashboard_events` | Consumes selected domain events, updates dashboard projection tables.                                  |

Each consumer has its own durable named queue and stores processed `event_id`
values in its service database. Reprocessing the same event is a no-op.

### 4.2 Scheduler sidecars

Scheduler sidecars run `infra/scripts/cron-runner.py`, which reads host-style
cron entries from `infra/cron/` and executes Django management commands inside
the service image.

| Sidecar              | Cron file                     | Schedule    | Command                                     | Purpose                                                                                 |
| -------------------- | ----------------------------- | ----------- | ------------------------------------------- | --------------------------------------------------------------------------------------- |
| `contract-scheduler` | `infra/cron/contract.crontab` | `0 4 * * *` | `python manage.py expire_contracts`         | Expire active contracts after their end date and publish `contract.expired`.            |
| `finance-scheduler`  | `infra/cron/finance.crontab`  | `0 2 1 * *` | `python manage.py generate_monthly_billing` | Create recurring monthly pending payments for active billing contracts.                 |
| `finance-scheduler`  | `infra/cron/finance.crontab`  | `0 3 * * *` | `python manage.py mark_overdue_payments`    | Mark past-due pending payments as overdue and publish `payment.overdue`.                |
| `booking-scheduler`  | `infra/cron/booking.crontab`  | `0 1 * * *` | `python manage.py complete_bookings`        | Complete approved bookings whose `end_time` has passed and publish `booking.completed`. |

This is the planned replacement for Celery. The project constraints explicitly
avoid Celery, so these sidecars provide recurring background work while keeping
the stack within Docker Compose and Django management commands.

### 4.3 Infrastructure sidecars and helper services

| Service                  | Purpose                                                                                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `minio-init`             | One-shot initialization for the MinIO document bucket.                                                                                                                                                             |
| `postgres` init script   | Initializes all service databases and users when the PostgreSQL volume is first created.                                                                                                                           |
| AppArmor Compose overlay | `infra/docker-compose.apparmor.yml` can set `apparmor=unconfined` for local hosts where Docker cannot access AppArmor profiles. This is a development/runtime compatibility layer, not part of the product domain. |

## 5. RabbitMQ architecture

### 5.1 Broker setup

RabbitMQ is configured with a durable topic exchange:

- Exchange: `incubator.events`
- Dead-letter exchange: `incubator.events.dead-letter`
- Default routing key: same as `event_type`
- Message envelope: JSON object with `event_id`, `event_type`, `occurred_at`, and `payload`

The shared implementation is in `libs/py-common/ilb_common/event_bus.py`.
Publishing uses durable messages with `delivery_mode=2`. Subscriptions use
manual acknowledgement. If a handler raises an exception, the message is
negative-acknowledged without requeue and can be routed to a dead-letter path for
durable queues.

Publishers generally call RabbitMQ from `transaction.on_commit`, so an event is
not sent if the local database transaction rolls back.

### 5.2 Event producers

| Producer service   | Events currently emitted                                                         |
| ------------------ | -------------------------------------------------------------------------------- |
| `company-service`  | `company.created`, `company.archived`, `employee.changed`                        |
| `contract-service` | `contract.activated`, `contract.terminated`, `contract.expired`                  |
| `booking-service`  | `booking.approved`, `booking.rejected`, `booking.cancelled`, `booking.completed` |
| `finance-service`  | `payment.recorded`, `payment.overdue`                                            |

Services that do not currently publish RabbitMQ events:

- `auth-service`
- `space-service`
- `inventory-service`
- `ticket-service`
- `dashboard-service`
- `document-service`

These services either own local request/response workflows or consume events
rather than publishing new integration events.

### 5.3 Event consumers

| Consumer sidecar     | Queue                      | Routing keys                                                                                                                                                                                                                     | Result                                                                                                |
| -------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `finance-consumer`   | `finance.contract-events`  | `contract.activated`, `contract.expired`, `contract.terminated`, `booking.approved`                                                                                                                                              | Maintains `BillingContract` rows and creates rental payment rows from approved bookings.              |
| `space-consumer`     | `space.domain-events`      | `contract.activated`, `contract.terminated`, `contract.expired`, `booking.approved`, `booking.rejected`, `booking.cancelled`, `booking.completed`                                                                                | Updates `SpaceContract` and `SpaceBookingRecord` projections and recomputes derived space status.     |
| `inventory-consumer` | `inventory.booking-events` | `booking.approved`, `booking.rejected`, `booking.cancelled`, `booking.completed`                                                                                                                                                 | Creates/releases equipment assignment records and toggles equipment availability.                     |
| `dashboard-consumer` | `dashboard.domain-events`  | `company.created`, `company.archived`, `employee.changed`, `contract.activated`, `contract.expired`, `contract.terminated`, `booking.approved`, `booking.rejected`, `booking.cancelled`, `booking.completed`, `payment.recorded` | Updates dashboard projection tables for companies, employees, contracts, bookings, and paid payments. |

### 5.4 Idempotency and reliability boundary

All implemented consumers store processed event ids in a `ProcessedEvent` table
inside their own database. This prevents duplicate RabbitMQ deliveries from
applying the same state transition twice.

Important reliability boundary: the project does not implement a full
transactional outbox pattern. Events are published after local commit through
`transaction.on_commit`, but they are still direct RabbitMQ publishes. If the
local database commit succeeds and RabbitMQ is unavailable at publish time, the
current code does not persist a local outbox record for later replay. This is
acceptable for the course/demo scope, but it is a known production-hardening
area.

## 6. Scheduler behavior

The implemented schedulers are intentionally small and idempotent:

### 6.1 Contract scheduler

- Runs daily at 04:00 Europe/Lisbon.
- Finds active contracts with `end_date` less than or equal to the current date.
- Calls the contract domain expiration method.
- Publishes `contract.expired` for each changed contract.
- Downstream effects are handled by `finance-consumer`, `space-consumer`, and
  `dashboard-consumer`.

### 6.2 Finance scheduler

It has two jobs:

1. Monthly billing generation at 02:00 on the first day of each month.
   - Creates pending payment rows for active billing contracts.
   - Skips existing monthly rows so the command can be rerun safely.
2. Daily overdue sweep at 03:00.
   - Finds pending payments with a due date before the selected day.
   - Marks them overdue.
   - Publishes `payment.overdue`.

### 6.3 Booking scheduler

- Runs daily at 01:00.
- Finds approved bookings whose end time has passed.
- Moves them to completed.
- Publishes `booking.completed`.
- Inventory and space projections release resources from the completed booking.

### 6.4 Dashboard rebuild command

`dashboard-service` includes `dashboard_rebuild`, but it is not wired to a cron
sidecar in the current Compose file. It is a manual/cold-start management
command that fetches upstream metric endpoints and stores JSON payloads in
`DashboardSnapshot` rows.

This command is useful after seeding or after starting an empty dashboard
database, but continuous dashboard updates primarily come from the
`dashboard-consumer` event sidecar and direct dashboard queries over projection
tables.

## 7. Dashboard architecture and Redis caching status

The dashboard implementation uses two data sources:

1. Materialized projection tables maintained by RabbitMQ events:
   - `CompanyProjection`
   - `EmployeeProjection`
   - `ContractProjection`
   - `BookingProjection`
   - `PaymentProjection`
   - `ProcessedEvent`
2. Snapshot JSON rows fetched from upstream service metric endpoints:
   - `DashboardSnapshot`

The dashboard API then calculates KPIs and chart payloads from these projection
and snapshot tables. For example, the overview endpoint derives active company
count, employee count, occupancy percentage, monthly revenue, overdue count,
pending bookings, and open tickets from projections and snapshots.

### 7.1 What Redis does today

Redis is present in Compose and passed as `REDIS_URL` in the shared Django
environment. However, explicit Redis cache configuration currently exists only
in `auth-service`:

- refresh-token JTI blacklist
- logout token revocation cache
- login/IP throttling cache
- DRF throttling cache for auth flows

The gateway has its own short Nginx auth cache, but that is not Redis.

### 7.2 What Redis does not do today

The original Phase 2 implementation plan mentioned Redis-backed caching for at
least two areas:

- `space-service` `/spaces/occupancy-map`, with a 10 second cache
- `dashboard-service` `/dashboard/overview`, with a 30 second cache

The current implementation does not fully satisfy those Redis-specific cache
requirements:

- `space-service` uses `django.core.cache.cache` around the occupancy-map
  response for 10 seconds, but `space-service` does not define a Redis-backed
  `CACHES` setting or include Redis client dependencies. In practice, this uses
  Django's default local-memory cache unless changed later.
- `dashboard-service` does not define a Redis-backed `CACHES` setting and does
  not cache `/dashboard/overview` in Redis. It recomputes from local projection
  tables and upstream metric calls.
- The public booking throttle is implemented with DRF throttling, but
  `booking-service` also does not define a Redis-backed `CACHES` setting. Its
  throttle is therefore local-memory unless a cache backend is added.

### 7.3 Why this was left this way

This appears to be a deliberate simplification for the course/demo boundary:

- Dashboard data is already mostly local to `dashboard_db` via materialized
  projections, so recomputation is not expensive on the seed/demo dataset.
- Avoiding Redis dashboard cache invalidation avoids stale KPI/chart values
  during live defense demos where actions are expected to update immediately.
- The architecture already demonstrates Redis through authentication token and
  throttle behavior.

However, if the original task list is graded literally for Redis cache on
`/dashboard/overview` and Redis-backed public booking throttling, this should be
called a known gap rather than a completed Redis caching feature.

## 8. Document storage

`document-service` owns document metadata in `document_db` and stores binary
objects in MinIO. The runtime provides:

- `minio` service for object storage
- `minio-init` for bucket setup
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, and
  `MINIO_USE_SSL` environment variables through Compose

This keeps documents out of PostgreSQL while still allowing document records,
company ownership, and authorization to stay in the Django service.

## 9. Production deployment shape

The production overlay `infra/docker-compose.production.yml` replaces local
build directives with registry images. It maps main services and sidecars to the
same built image tag where appropriate. Examples:

- `contract-service` and `contract-scheduler` use the same contract image.
- `finance-service`, `finance-consumer`, and `finance-scheduler` use the same
  finance image.
- `booking-service` and `booking-scheduler` use the same booking image.
- `dashboard-service` and `dashboard-consumer` use the same dashboard image.

The CI deployment scripts map changed deployable images to the Compose services
that must be restarted. For example, changing `finance-service` restarts
`finance-service`, `finance-consumer`, and `finance-scheduler`.

## 10. Items intentionally not done or implemented differently from the original plan

This section separates hard constraints from known deviations.

### 10.1 Celery, Kubernetes, and cloud services

Not implemented on purpose.

Reason: the project constraints explicitly required no Celery, no Kubernetes,
and no cloud services. The replacement is:

- Docker Compose for orchestration
- Django management commands for background jobs
- scheduler sidecars for cron-style recurring work
- RabbitMQ consumer sidecars for asynchronous event processing
- MinIO as local S3-compatible object storage

### 10.2 Redis dashboard caching

Partially not implemented, as detailed in section 7.

The plan mentioned Redis cache for dashboard overview and space occupancy. The
current architecture uses Redis for auth, but dashboard caching is projection and
snapshot based rather than Redis based. Space occupancy has a cache wrapper, but
not a Redis backend in that service.

This should be documented as a known deviation. It is acceptable for a small
seeded demo because dashboard reads are local database queries, but it is not the
same as the planned Redis cache acceptance criteria.

### 10.3 Dashboard aggregate model names

Implemented differently.

The plan listed conceptual materialized stats such as company stats, space
stats, financial summary, revenue series, employee stats, and booking stats. The
actual implementation uses event projection tables:

- `CompanyProjection`
- `EmployeeProjection`
- `ContractProjection`
- `BookingProjection`
- `PaymentProjection`
- `DashboardSnapshot`

Dashboard endpoints compute the final aggregates from those projections. This is
a reasonable design choice because it preserves drill-down flexibility, but the
physical table names do not match the conceptual task names one-for-one.

### 10.4 Dashboard event coverage

Partially implemented.

The dashboard consumer handles company, employee, contract, booking, and
`payment.recorded` events. It does not currently consume `payment.overdue`, and
support tickets do not publish ticket domain events. Ticket indicators are
instead read through ticket metrics snapshots.

This means dashboard open-ticket and overdue-payment indicators depend on
snapshot/metric pulls rather than a fully event-driven ticket/payment-overdue
projection. For the demo architecture this is sufficient, but it is not a fully
event-sourced dashboard.

### 10.5 Transactional outbox

Not implemented.

RabbitMQ publishing is done after transaction commit, but no service stores
outgoing events in a durable local outbox table. A production-grade extension
would add per-service outbox tables and a relay process so broker outages cannot
lose integration events after local database commits.

### 10.6 SSL termination

Not implemented inside this repository.

The gateway listens for HTTP. The original requirement said SSL termination
should be handled if applicable. For the course VM and local demo, plain HTTP on
port 80 was used. If TLS is required, it should be added at the gateway or in a
fronting reverse proxy/load balancer with certificate management.

### 10.7 Backend and frontend i18n completeness

Not fully completed by project direction.

The frontend contains Portuguese text and dictionaries in several areas, but the
full original i18n task set was later deprioritized. Backend gettext coverage
for every error message and a complete runtime language toggle were not treated
as release blockers.

### 10.8 Full observability stack

Not implemented.

Each service has health endpoints and metrics stubs, and the dashboard checks
service health/metrics endpoints. There is no Prometheus server, Grafana,
distributed tracing, alerting, or centralized log aggregation. This is outside
the course implementation scope but would be a production-hardening item.

### 10.9 Physical database server per service

Implemented as logical separation rather than physical separation.

Each service has its own database and user, but all databases run inside one
PostgreSQL container. This keeps deployment lightweight while preserving service
schema isolation. A stricter production interpretation could use one PostgreSQL
instance per service, but that was not necessary for this project.

## 11. Summary of current architecture quality

The implemented architecture satisfies the central microservices requirements:

- More than four services, with multiple core business services.
- DRF APIs and Django ORM migrations per service.
- Separate logical PostgreSQL databases per service.
- JWT authentication and role/company scoping through the gateway.
- RabbitMQ topic exchange with documented event envelope.
- Consumer idempotency through `ProcessedEvent` tables.
- Scheduler sidecars instead of Celery.
- Docker Compose based infrastructure with PostgreSQL, Redis, RabbitMQ, MinIO,
  Nginx gateway, frontend, and service sidecars.
- A deployment overlay that reuses service images for sidecars.

The main architectural caveats to be transparent about are:

1. Redis is not used for dashboard overview caching, and only `auth-service` has
   explicit Redis cache configuration.
2. `space-service` and `booking-service` cache/throttle behavior is currently
   local-memory unless cache settings are extended.
3. Dashboard is a hybrid of event projections and metric snapshots, not a fully
   event-driven cache of every domain signal.
4. There is no durable transactional outbox for outgoing integration events.
5. TLS, advanced observability, and physical DB-per-service infrastructure are
   outside the current Docker Compose course scope.

These caveats do not break the implemented demo flows, but they should be stated
clearly during technical discussion so the architecture is represented accurately.
