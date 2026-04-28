# Contributing

Conventions for branches, commits, and merge requests in this monorepo.

## Branch naming

Use one branch per task, named:

```text
w<week>/<short-slug>
```

Examples: `w1/compose-stack`, `w2/ci-e2e-pipeline`. Slugs are lowercase with hyphens;
avoid generic names like `fix` or `wip`.

## Commits (Conventional Commits)

Write commit subjects in **English**, imperative mood, **≤ 72 characters**:

```text
<type>(<scope>): <subject>
```

Common **types**: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`.

**Scopes** match the area touched, for example: `infra`, `gateway`, `compose`,
`auth-service`, `frontend`, `ci`. Use a single scope when possible.

Examples:

- `feat(gateway): forward role headers to upstream`
- `fix(compose): pin postgres image digest`
- `docs(cross): contributing, deploy, and quickstart`

Squash-merge produces one commit on `main`; keep MR commits readable even if they
are squashed.

## Merge requests

- One MR per task; prefer draft until CI is green.
- MR title equals the squash-merge commit subject (conventional line above).
- MR description: short technical summary and an acceptance checklist for
  reviewers—no unrelated discussion threads.

## Language

- Code, comments, commits, and MR titles/descriptions: **English**.
- End-user UI strings: **pt-PT** via i18n where applicable.

## Lint and tests before review

Install tooling (see root `README.md`) and run:

```bash
pre-commit run --all-files
make lint
```

Align with CI (GitLab pipeline and/or `.github/workflows/` mirrors).
