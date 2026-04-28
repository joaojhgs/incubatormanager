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
