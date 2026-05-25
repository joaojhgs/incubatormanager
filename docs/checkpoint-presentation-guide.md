# Checkpoint Presentation Guide

**Updated:** 2026-05-25  
**Project:** ILB — Business Incubator Management Platform

## One-line status

Phase 2 has been brought to an integration-ready local state: the remaining Contract, Finance, Space, Booking, Inventory, Ticket, Dashboard, and frontend placeholder-replacement work has landed in the repository and is covered by targeted local checks.

## Architecture summary

- Ten Django/DRF services in one monorepo.
- One database per service.
- Nginx gateway validates auth through Auth and injects identity headers.
- RabbitMQ topic exchange carries event envelopes for cross-service workflows.
- Next.js 14 + Ant Design v5 frontend provides staff/client/public surfaces.

## Demo story to show

1. Staff views service dashboard and operational pages.
2. Company data is visible with employees, maturity, and stats.
3. Contract activation emits the business event used by Finance and Space projections.
4. Finance creates/records payments and exposes dashboard/report data.
5. Space/Booking/Inventory demonstrate availability, booking lifecycle, and equipment assignment.
6. Client-scoped ticket/payment/booking views respect `X-Company-Id` isolation.

## Local verification to cite

Use local evidence instead of shared CI runner status:

- Backend service `manage.py check` and targeted pytest suites.
- Migration dry-runs for services with model changes.
- Frontend typecheck, unit tests, lint, and build.
- Integration smoke checks and `make demo` before the final presentation.

## Key risks to be transparent about

- Full Docker demo and end-to-end browser coverage must be rerun after any final merge/rebase.
- Service projections depend on event payload shape consistency.
- Dashboard data is a lightweight aggregation layer; keep the <2s target in local smoke checks.
