# Architecture

This document describes how the ILB Incubator Platform is decomposed into
services, how they integrate, and how the **Company** bounded context relates to
the rest of the system. Operational runbooks live in `docs/deploy.md`; branch
and commit conventions in `docs/contributing.md`.

## 1. Services and integration

The repository is a **monorepo** of **strict microservices**: one deployable
Django application per bounded context, each with its **own PostgreSQL
database**. Services do not share ORM models or database schemas. Where one
context needs data owned by another, it uses **synchronous HTTP** (through the
gateway) and/or **asynchronous messaging** on RabbitMQ.

### 1.1 Service catalogue

| Service (compose name) | Bounded context                                                       | Gateway path prefix | Internal port | Database       |
| ---------------------- | --------------------------------------------------------------------- | ------------------- | ------------- | -------------- |
| `auth-service`         | Identity, sessions, JWT issuance and validation                       | `/api/auth/`        | 8001          | `auth_db`      |
| `company-service`      | Incubated **companies**, profiles, CAE, lifecycle (including archive) | `/api/companies/`   | 8002          | `company_db`   |
| `contract-service`     | Contracts with incubated companies                                    | `/api/contracts/`   | 8003          | `contract_db`  |
| `finance-service`      | Billing and financial records                                         | `/api/finance/`     | 8004          | `finance_db`   |
| `space-service`        | Physical spaces and resources                                         | `/api/spaces/`      | 8005          | `space_db`     |
| `booking-service`      | Bookings for spaces (includes selected unauthenticated routes)        | `/api/bookings/`    | 8006          | `booking_db`   |
| `inventory-service`    | Inventory items                                                       | `/api/inventory/`   | 8007          | `inventory_db` |
| `ticket-service`       | Support tickets                                                       | `/api/tickets/`     | 8008          | `ticket_db`    |
| `dashboard-service`    | Aggregated dashboards                                                 | `/api/dashboard/`   | 8009          | `dashboard_db` |
| `document-service`     | Document metadata and storage integration (MinIO)                     | `/api/documents/`   | 8010          | `document_db`  |

All backend ports are **internal to the Docker network** only. External clients
and the Next.js **frontend** call a single **Nginx gateway**, which routes by
path prefix to the correct upstream. JWT validation uses `auth_request` against
`auth-service`; on success, trusted headers (`X-User-Id`, `X-User-Role`,
`X-Company-Id`) are forwarded to upstreams. See `gateway/nginx.conf` for the
canonical routing table.

The **frontend** is a separate Next.js 14 (App Router) application; it is
served through the gateway on `/` while API traffic uses `/api/...`.

### 1.2 Synchronous calls

Service-to-service and browser-to-API communication uses **REST** (Django REST
Framework) under the gateway. OpenAPI descriptions are exposed per service where
applicable (`schema.yml`); clients may generate TypeScript types from those
schemas. Keep synchronous calls for request/response flows that must complete
in-line with a user action or a single API request.

### 1.3 Asynchronous events

Cross-cutting notifications and eventual consistency use the **`incubator.events`**
topic exchange on RabbitMQ. Publishers and consumers use the shared envelope
implemented in `libs/py-common` (`ilb_common.event_bus`):

- **`event_id`**: UUID string; consumers must treat processing as **idempotent**
  on `event_id` (skip or upsert if already handled).
- **`event_type`**: Dot-separated name (matches the routing key unless
  overridden).
- **`occurred_at`**: ISO-8601 timestamp in UTC (with `Z` suffix).
- **`payload`**: JSON object; schema is defined per `event_type`.

The default routing key equals `event_type`. Durable messages (`delivery_mode=2`)
are used so brokers can survive restarts. Where publishing follows a database
write, emit **inside** `transaction.on_commit` so messages are not sent if the
transaction rolls back.

Background work does **not** use Celery: scheduled or recurring work runs via
**management commands** invoked from **scheduler sidecar** containers using
host-style cron (`infra/cron/`).

### 1.4 Shared infrastructure (summary)

- **PostgreSQL 16**: one logical database per service; dedicated DB users with
  least privilege.
- **Redis**: caching, JWT deny-list, and rate limiting (as configured per
  service).
- **MinIO**: S3-compatible object storage for documents (bucket contract in
  environment variables).
- **Timezone**: **`Europe/Lisbon`** for all containers (`TZ`).

---

## 2. Company bounded context and events

### 2.1 Ownership

The **company-service** is the **authoritative** source for the **Company**
aggregate: incubated organisation identity, commercial and CAE-related fields,
maturity and status, and **archival** state. Other services store **foreign
keys** (UUID `company_id`) and any denormalized display fields they need, but
they must not become the system of record for whether a company exists or is
archived.

User accounts suitable for login and JWTs live under **auth-service**; links
between a person and a company (e.g. staff assignment, client contact, or
role on a company) are modelled in the owning contexts—when a change must be
visible across services, those teams rely on **API queries** and **domain
events** rather than shared tables.

### 2.2 Integrating with Company data

- Prefer **reading** company attributes through **company-service** APIs when
  enforcing rules in another bounded context.
- For **read models** and denormalized caches (dashboard, search, etc.),
  subscribe to **Company-related events** (below) and refresh idempotently.

### 2.3 Event catalogue (SDL Phase 2 domain set)

The following event types are part of the platform catalogue; full payload
contracts and publisher notes are summarised in `docs/events.md`.

| `event_type`       | Summary                                                                                                                                                                            |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `company.created`   | New company created; downstream services may create company-scoped state and indexes. |
| `company.archived`  | A company has been moved to an archived state; downstream services should stop treating it as active for operational workflows and may tighten access.                             |
| `employee.changed`  | Employment or affiliation data for a person relative to a company has changed (e.g. role, assignment, or end of association); consumers refresh denormalized person–company views. |
| `contract.activated` | Contract entered active state for a company/space pair; consumers can create/update billing and availability state. |
| `contract.terminated` | Contract terminated early; consumers should unblock future booking windows and recompute financial status. |
| `contract.expired`   | Contract reached end date without termination; consumers should deactivate operational availability. |
| `booking.approved`   | Booking approved and ready for service execution; consumers may reserve inventory and prepare billing state. |
| `booking.rejected`   | Booking rejected; consumers should release tentative reservations and invalidate pending booking-side state. |
| `booking.cancelled`  | Booking cancelled and must release resources and block execution. |
| `booking.completed`  | Booking completed and can trigger final invoice and occupancy reconciliation. |
| `payment.recorded`   | Payment recorded in finance; consumers should refresh financial aggregates. |

Both use the standard envelope in §1.3. Naming is stable: new subscribers **must
not** infer different semantics for the same `event_type`.
