# Domain events catalogue

RabbitMQ **topic exchange:** `incubator.events`

All messages use the JSON envelope implemented in `libs/py-common`
(`event_id`, `event_type`, `occurred_at`, `payload`).
The default **routing key** equals `event_type`.

Consumers must be **idempotent** on `event_id` (reprocess checks must be a no-op).

See `docs/architecture.md` for platform context and integration rules.

## Event contract and consumer expectations

### `company.created`

- **When:** After a company has been successfully created in `company-service`.
- **Routing key:** `company.created`
- **Suggested payload:**
  - `company_id` (UUID, required)
  - `name` (string)
  - `cae_id` (UUID)
  - `cae_code` (string)
  - `maturity_stage_id` (UUID)
  - `maturity_stage_name` (string)
- **Typical consumers:** ticketing, finance, space, booking, dashboard and any cache that keys by company identity.

### `company.archived`

- **When:** After a company has been successfully archived in `company-service`.
- **Routing key:** `company.archived`
- **Suggested payload:**
  - `company_id` (UUID, required)
  - `archived_at` (ISO-8601 datetime, required)
  - `reason` (string, optional)
- **Typical consumers:** services that gate operational actions on active companies.

### `employee.changed`

- **When:** A person’s affiliation or role changes relative to a company in
  `company-service`.
- **Routing key:** `employee.changed`
- **Suggested payload:**
  - `company_id` (UUID, required)
  - `employee_id` (UUID)
  - `action` (string, for example `created`, `updated`, `deleted`)
  - `employee_type` (string)
- **Typical consumers:** dashboard and any view materializations that project workforce data.

### `contract.activated`

- **When:** Contract enters active state in `contract-service`.
- **Routing key:** `contract.activated`
- **Suggested payload:**
  - `contract_id` (UUID, required)
  - `company_id` (UUID)
  - `space_id` (UUID)
  - `area_sqm` (decimal)
  - `rate_per_sqm` (decimal)
  - `monthly_fee` (decimal)
  - `start_date` (ISO-8601 date)
  - `end_date` (ISO-8601 date)
- **Typical consumers:** finance, space, booking, dashboard.

### `contract.expired`

- **When:** Contract reaches its configured end in `contract-service`.
- **Routing key:** `contract.expired`
- **Suggested payload:**
  - `contract_id` (UUID, required)
  - `company_id` (UUID)
  - `space_id` (UUID)
- **Typical consumers:** finance, dashboard, booking.

### `contract.terminated`

- **When:** Contract is terminated before schedule end in `contract-service`.
- **Routing key:** `contract.terminated`
- **Suggested payload:**
  - `contract_id` (UUID, required)
  - `company_id` (UUID)
  - `space_id` (UUID)
  - `reason` (string)
- **Typical consumers:** finance, space, booking, dashboard.

### `booking.approved`

- **When:** Booking approved in `booking-service`.
- **Routing key:** `booking.approved`
- **Suggested payload:**
  - `booking_id` (UUID, required)
  - `company_id` (UUID)
  - `space_id` (UUID)
  - `start_time` (ISO-8601 datetime)
  - `end_time` (ISO-8601 datetime)
  - `quoted_price` (decimal)
  - `equipment_ids` (array UUIDs)
- **Typical consumers:** space, inventory, finance, dashboard.

### `booking.rejected`

- **When:** Booking rejected in `booking-service`.
- **Routing key:** `booking.rejected`
- **Suggested payload:**
  - `booking_id` (UUID, required)
  - `company_id` (UUID)
  - `space_id` (UUID)
- **Typical consumers:** space, dashboard.

### `booking.cancelled`

- **When:** Booking cancelled in `booking-service`.
- **Routing key:** `booking.cancelled`
- **Suggested payload:**
  - `booking_id` (UUID, required)
  - `company_id` (UUID)
  - `space_id` (UUID)
  - `equipment_ids` (array UUIDs)
- **Typical consumers:** space, inventory, finance, dashboard.

### `booking.completed`

- **When:** Booking marked complete in `booking-service`.
- **Routing key:** `booking.completed`
- **Suggested payload:**
  - `booking_id` (UUID, required)
  - `company_id` (UUID)
  - `space_id` (UUID)
  - `equipment_ids` (array UUIDs)
- **Typical consumers:** space, inventory, dashboard.

### `payment.recorded`

- **When:** Payment recorded in `finance-service`.
- **Routing key:** `payment.recorded`
- **Suggested payload:**
  - `payment_id` (UUID, required)
  - `company_id` (UUID)
  - `contract_id` (UUID)
  - `booking_id` (UUID)
  - `amount` (decimal)
  - `paid_at` (ISO-8601 datetime)
- **Typical consumers:** dashboard, reporting, finance reconciliation flows.
