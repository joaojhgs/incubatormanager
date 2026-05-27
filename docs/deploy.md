# Deployment notes

Operational overview for running the ILB stack from this repository with Docker
Compose. For local live reload, use Tilt (`tilt up`); it is **development-only**
and not a substitute for this compose-based layout.

## Topology

- **Gateway:** Nginx (`gateway` service) terminates HTTP on host port **80** →
  container port `8080`. Routes `/api/...` to Django services and serves the
  Next.js **frontend** build.
- **Data plane:** Single PostgreSQL 16 instance with **one logical database per
  service**; Redis; RabbitMQ (topic exchange `incubator.events`); MinIO
  (S3-compatible document bucket).
- **Services:** Django apps listen on **8001–8010** inside the Docker network
  only; they are not published to the host except via the gateway paths under
  `/api/...`.

Timezone for containers is **`Europe/Lisbon`** (`TZ` in compose).

## Preconditions

- Docker Engine and Compose v2 on the host.
- Repository checkout and a populated **`.env`** at the repo root (see
  `.env.example`). Never commit real secrets.

Minimum variables to review before production-shaped runs:

- **PostgreSQL:** `POSTGRES_PASSWORD` and each `*_DB_PASSWORD` (per-service DB
  users are created by init scripts).
- **Django:** `DJANGO_SECRET_KEY` (unique per environment).
- **MinIO:** `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, and bucket usage for
  documents.
- **Frontend:** `NEXT_PUBLIC_API_URL` must point at the gateway origin users
  hit in the browser (e.g. `https://your-host/api` when TLS terminates in front
  of the gateway).

Adjust firewall rules so only the gateway (port 80 or your TLS terminator) is
exposed as needed; internal service ports should remain on the Docker network.

## Start and stop

From the repository root:

```bash
cp .env.example .env
# edit .env for your environment

make up      # background: docker compose --project-directory . -f infra/docker-compose.yml up -d --build
make down    # stop containers
make logs    # follow logs
make ps      # service status
```

Health checks are defined in `infra/docker-compose.yml`; wait until services are
healthy before sending traffic.

## Smoke checks

Through the gateway (default local URL):

```bash
curl -fsS http://localhost/health
curl -fsS http://localhost/api/auth/health
```

Replace `localhost` with your hostname when deployed remotely.

## Backups and retention

- **Postgres:** back up volume data or use your organisation’s DB backup policy
  for the `postgres-data` volume / server snapshot strategy.
- **MinIO:** treat object storage like production data; mirror your NFRs for
  retention and restore.
- **Secrets:** supply via environment or a secrets manager; rotate DB and MinIO
  credentials on compromise or cadence per policy.

## CI

GitLab CI (`.gitlab-ci.yml` and `.gitlab/ci/`) builds and tests on push/MR; keep
compose definitions aligned with what CI validates when you change images or
health endpoints.

## GitLab production deployment

### Registry-based changed-service rollout

The production pipeline now separates changed-service detection, image build/push,
and remote deployment:

1. `changed:services` writes `DEPLOY_IMAGES` and `DEPLOY_COMPOSE_SERVICES` from
   the Git diff.
2. `build:changed-images` builds only `DEPLOY_IMAGES` and pushes them to the
   GitLab container registry as `${CI_REGISTRY_IMAGE}/<service>:${CI_COMMIT_SHA}`.
3. `deploy:production` SSHes to the Docker host, copies the release compose
   files, logs in to the registry, pulls the changed compose services, and runs
   `docker compose up -d --no-build` for only those services.

Required protected GitLab CI/CD variables for automatic production deployment
from `main`:

- `DEPLOY_HOST` — SSH host/IP of the production Docker machine.
- `DEPLOY_USER` — SSH user with permission to run Docker Compose.
- `DEPLOY_SSH_PRIVATE_KEY` — private key for that user.
- `DEPLOY_PATH` — release root on the host, for example `/opt/ilb`.
- `DEPLOY_ENV_FILE_BASE64` or `DEPLOY_ENV_FILE` — production `.env` content.

Optional variables:

- `DEPLOY_KNOWN_HOSTS` — pinned SSH known-hosts entry.
- `PRODUCTION_URL` — GitLab environment URL shown in the Environments page.

The remote host must already have Docker Engine and the Docker Compose plugin.
The first deployment creates `${DEPLOY_PATH}/current`, `${DEPLOY_PATH}/releases`,
and `${DEPLOY_PATH}/shared/.env`. Later deployments reuse the shared `.env` unless
one of the `DEPLOY_ENV_*` variables is supplied again.
