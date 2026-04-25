# syntax=docker/dockerfile:1
#
# Build from the monorepo root (standalone trace paths match `frontend/package.json`):
#   docker build -f frontend/Dockerfile -t incubator-frontend .

# --- install dependencies (cached when lockfiles are unchanged) ---
FROM node:20.18.1-bookworm-slim AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# --- production build (Next standalone output) ---
FROM node:20.18.1-bookworm-slim AS builder
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
# Next.js serves static files from this directory; it may be absent in the repo
RUN mkdir -p public
RUN npm run build

# --- run node server from traced standalone bundle ---
FROM node:20.18.1-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates wget \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd --gid 1001 nodejs \
  && useradd --uid 1001 --gid nodejs --shell /bin/false --create-home nextjs
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -qO- "http://127.0.0.1:3000/login" >/dev/null 2>&1 || exit 1
CMD ["node", "server.js"]
