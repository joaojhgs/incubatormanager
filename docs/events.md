# Domain events catalogue

RabbitMQ **topic exchange:** `incubator.events`

All messages use the JSON envelope implemented in `libs/py-common`
(`event_id`, `event_type`, `occurred_at`, `payload`). The default **routing
key** equals `event_type`. Consumers must be **idempotent** on `event_id`.

See `docs/architecture.md` for platform context and integration rules.

## Events

### `company.archived`

- **When:** After a company has been successfully archived in **company-service**
  (transaction committed).
- **Typical publishers:** `company-service`.
- **Suggested `payload` fields (evolving):**
  - `company_id` (UUID, required)
  - `archived_at` (ISO-8601 datetime, required)
  - `reason` (string, optional; internal categorisation if used)
- **Consumers:** services that gate bookings, contracts, finance, or UI on
  active companies should invalidate caches and block new operational actions
  against archived companies while retaining historical data as required.

### `employee.changed`

- **When:** A person’s affiliation or role **relative to a company** changes in
  a way other bounded contexts must observe (e.g. contact, incubation staff
  assignment, or end of relationship). Exact triggering rules are defined in
  **company-service** (and related services if they co-publish).
- **Typical publishers:** `company-service` (primary); possibly **auth-service**
  for pure credential changes that still affect company-linked staff views—teams
  must avoid duplicate publication for the same logical change.
- **Suggested `payload` fields (evolving):**
  - `user_id` (UUID, required) — platform user
  - `company_id` (UUID, optional) — set when the change is scoped to one
    company; omit or null when the change is global (e.g. platform-only role)
  - `changed` (array of string field names or a structured object, required) —
    what downstream denormalizations should refresh
- **Consumers:** dashboard, ticketing, or booking flows that show
  person–company relationships; refresh materialised views idempotently.
