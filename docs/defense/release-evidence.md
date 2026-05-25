# Defense/Release Evidence

Updated: 2026-05-25

This document is the release-facing evidence index for the Phase 2 defense branch. It links the required gates, current command evidence, functional smoke expectations, and known environment blockers. Keep it current before a defense run or release handoff.

## Release criteria

A release or defense handoff is ready only when the following are true:

- Host-only quality gate has a current PASS or an explicit blocker with owner.
- Docker compose gate has a current PASS on a machine with Docker socket access.
- Frontend typecheck, unit tests, lint, and production build pass before browser e2e is treated as product evidence.
- Gateway Playwright smoke passes against a seeded live stack, or the blocker is recorded as environment-only.
- `docs/user.md`, `docs/defense/demo-script.md`, and `docs/defense/checklist.md` match the demonstrated workflow.
- No secrets, `.env` contents, tokens, generated private recordings, or unapproved binary artifacts are committed.

## Command evidence log

| Date       | Command                              | Result                                                                                                                                 | Next step                                                       |
| ---------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 2026-05-25 | `make local-gate-host`               | PASS: lint, format, frontend typecheck/unit/build, infra tests, shared library tests, and all backend service migration/pytest checks. | Rerun after every release-candidate change.                     |
| 2026-05-25 | `npm --prefix frontend run test:e2e` | PASS: 11 Playwright tests covering login, portal scoping, dashboard, inventory, public booking validation, and user flows.             | Keep as the non-Docker browser smoke gate.                      |
| 2026-05-25 | `make demo`                          | BLOCKED: Docker socket permission denied before application startup.                                                                   | Rerun on a host with Docker socket access.                      |
| 2026-05-25 | `npm run test:e2e`                   | BLOCKED: gateway suite received `ECONNREFUSED 127.0.0.1:80` because compose was not running.                                           | Rerun after `make demo` or `make up` succeeds on a Docker host. |

## Functional smoke checklist by domain

| Domain    | Smoke expectation                                                                                                  | Evidence source                                        |
| --------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| Auth/User | Staff and client users can sign in; protected routes redirect unauthenticated users.                               | Frontend Playwright login and user-management smoke.   |
| Company   | Staff can list/detail companies; client portal shows only the authenticated company.                               | Staff Companies page and Client Company page.          |
| Document  | Company/client document sections show available metadata and upload/list/download integration points where seeded. | Company/client document walkthrough.                   |
| Contract  | Staff contract list and client contract view show status, company, space, and fee data.                            | Staff Contracts and Client Contract pages.             |
| Finance   | Staff finance dashboard shows total/paid/pending/overdue values; client payments are company-scoped.               | Staff Finance and Client Payments pages.               |
| Space     | Staff space page shows capacity, occupancy, active booking, and next booking context.                              | Staff Spaces page.                                     |
| Booking   | Public request remains unauthenticated; staff and client booking views show scoped records.                        | Public booking route plus Staff/Client Bookings pages. |
| Inventory | Staff inventory page shows equipment status, assignment, booking, and space projection information.                | Staff Inventory page and browser smoke.                |
| Ticket    | Staff tickets show support queue; client tickets show only the client user's requests.                             | Staff Tickets and Client Tickets pages.                |
| Dashboard | Staff dashboard shows cross-service operational aggregates and drill-through links.                                | Staff Dashboard page and browser smoke.                |

## Environment assumptions and blockers

- Docker-backed commands require a host user that can access `/var/run/docker.sock`. If that permission is missing, record the exact command and error and use the backup recording path in `docs/defense/demo-script.md`.
- The root gateway Playwright suite requires a live compose gateway at `127.0.0.1:80`; it is not a standalone mocked browser suite.
- Frontend dependency audit warnings are from the existing lockfile and should be handled in a dependency/security update lane.
- Demo credentials belong in private operator notes or local environment files, not in repository docs.

## Sign-off

Before final sign-off, update this section with:

- Release branch or commit SHA.
- Person running the gate.
- Host used for Docker-backed evidence.
- PASS/FAIL summary for host-only gate, compose gate, browser smoke, and demo walkthrough.
- Links or paths to any approved external recording or exported slide artifact.
