# SDL Phase 2 Review Notes (Task 3)

Date: 2026-05-25

## Scope checked
- Reviewed implementation status against `.omx/plans/prd-phase2-remaining-sdl.md` and
  `.omx/plans/test-spec-phase2-remaining-sdl.md`.
- Focused on code-quality and documentation updates in the canonical leader repo.

## Findings (from repository snapshot)

### Backend route readiness
- Company service exposes real non-health routes for companies/CAE/maturity via
  `core/urls.py`.
- Ticket service has CRUD/my/message routes and is the only domain beyond health checks.
- Booking, Contract, Finance, Space, Inventory, and Dashboard services currently
  only expose health endpoints and schema descriptions; these remain pending
  implementation work.

### Frontend placeholders
- Staff placeholders remain in:
  - `frontend/app/(staff)/spaces/page.tsx`
  - `frontend/app/(staff)/finance/page.tsx`
  - `frontend/app/(staff)/bookings/page.tsx`
  - `frontend/app/(staff)/tickets/page.tsx`
  - `frontend/app/(staff)/contracts/page.tsx`
  - `frontend/app/(staff)/inventory/page.tsx`
- Client placeholders remain in:
  - `frontend/app/(client)/portal/bookings/page.tsx`
  - `frontend/app/(client)/portal/tickets/page.tsx`
  - `frontend/app/(client)/portal/payments/page.tsx`
  - `frontend/app/(client)/portal/contract/page.tsx`
  - `frontend/app/(client)/portal/company/page.tsx`

### Test surface currently present
- Ticket service has non-health endpoint tests.
- Company service has company/CAE/maturity endpoint tests.
- Other phase domains (booking/contract/finance/space/inventory/dashboard) have only `test_health.py` plus a stub seed test in space.
- This indicates missing regression coverage for the intended Phase 2 endpoint and
  event flows.

### Service contract docs quality
- Multiple service `schema.yml` and `settings.py` descriptions still referenced
  these APIs as "stub" despite broader PRD requirements; these were updated in
  this task.
- Event catalogue docs were missing most phase-2 events and payload notes; updated
  in `docs/events.md` and mirrored in `docs/architecture.md`.

## Actionable documentation updates made in this task
1. `docs/events.md`: completed event matrix with required SDL phase-2 event types and
   suggested payload fields.
2. `docs/architecture.md`: expanded the architecture event catalogue to match SDL
   phase-2 event set.
3. Service metadata docs (`schema.yml` + `settings.py` `SPECTACULAR_SETTINGS.DESCRIPTION`):
   removed outdated "stub" suffix across phase-2 services.

