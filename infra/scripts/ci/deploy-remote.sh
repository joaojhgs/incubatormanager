#!/usr/bin/env bash
# Deploy changed images to a remote Docker host through SSH and Docker Compose.
set -euo pipefail

: "${DEPLOY_HOST:?Set DEPLOY_HOST as a protected GitLab CI variable}"
: "${DEPLOY_USER:?Set DEPLOY_USER as a protected GitLab CI variable}"
: "${DEPLOY_PATH:?Set DEPLOY_PATH as a protected GitLab CI variable}"
: "${DEPLOY_SSH_PRIVATE_KEY:?Set DEPLOY_SSH_PRIVATE_KEY as a protected GitLab CI variable}"
: "${CI_REGISTRY_IMAGE:?CI_REGISTRY_IMAGE is required}"
: "${CI_REGISTRY:?CI_REGISTRY is required}"
: "${CI_REGISTRY_USER:?CI_REGISTRY_USER is required}"
: "${CI_REGISTRY_PASSWORD:?CI_REGISTRY_PASSWORD is required}"

image_tag="${IMAGE_TAG:-${CI_COMMIT_SHA:-latest}}"
compose_services="${DEPLOY_COMPOSE_SERVICES:-}"
if [[ -z "$compose_services" ]]; then
  echo "No changed compose services to deploy."
  exit 0
fi

ssh_target="${DEPLOY_USER}@${DEPLOY_HOST}"
ssh_opts=()
mkdir -p ~/.ssh
chmod 700 ~/.ssh
if [[ -n "${DEPLOY_SSH_PRIVATE_KEY:-}" ]]; then
  printf '%s\n' "$DEPLOY_SSH_PRIVATE_KEY" > ~/.ssh/deploy_key
  chmod 600 ~/.ssh/deploy_key
  ssh_opts+=(-i ~/.ssh/deploy_key -o IdentitiesOnly=yes)
fi
if [[ -n "${DEPLOY_KNOWN_HOSTS:-}" ]]; then
  printf '%s\n' "$DEPLOY_KNOWN_HOSTS" > ~/.ssh/known_hosts
  chmod 600 ~/.ssh/known_hosts
else
  ssh_opts+=(-o StrictHostKeyChecking=accept-new)
fi
remote_release="${DEPLOY_PATH}/releases/${image_tag}"
remote_current="${DEPLOY_PATH}/current"

echo "Preparing remote release ${remote_release}"
ssh "${ssh_opts[@]}" "$ssh_target" "mkdir -p '${remote_release}' '${DEPLOY_PATH}/shared'"

tar \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/.next' \
  -czf - \
  .env.example infra gateway docker-compose.tilt.yml Tiltfile README.md docs \
  | ssh "${ssh_opts[@]}" "$ssh_target" "tar -xzf - -C '${remote_release}'"

if [[ -n "${DEPLOY_ENV_FILE_BASE64:-}" ]]; then
  printf '%s' "$DEPLOY_ENV_FILE_BASE64" | base64 -d | ssh "${ssh_opts[@]}" "$ssh_target" "cat > '${DEPLOY_PATH}/shared/.env'"
elif [[ -n "${DEPLOY_ENV_FILE:-}" ]]; then
  printf '%s\n' "$DEPLOY_ENV_FILE" | ssh "${ssh_opts[@]}" "$ssh_target" "cat > '${DEPLOY_PATH}/shared/.env'"
else
  ssh "${ssh_opts[@]}" "$ssh_target" \
    "test -f '${DEPLOY_PATH}/shared/.env' || cp '${remote_release}/.env.example' '${DEPLOY_PATH}/shared/.env'"
fi

registry_password_escaped="$(printf '%s' "$CI_REGISTRY_PASSWORD" | sed "s/'/'\\''/g")"
ssh "${ssh_opts[@]}" "$ssh_target" "docker login '${CI_REGISTRY}' -u '${CI_REGISTRY_USER}' -p '${registry_password_escaped}'"

ssh "${ssh_opts[@]}" "$ssh_target" \
  "ln -sfn '${remote_release}' '${remote_current}' && cd '${remote_current}' && ln -sfn '${DEPLOY_PATH}/shared/.env' .env && IMAGE_TAG='${image_tag}' CI_REGISTRY_IMAGE='${CI_REGISTRY_IMAGE}' docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.production.yml pull ${compose_services} && IMAGE_TAG='${image_tag}' CI_REGISTRY_IMAGE='${CI_REGISTRY_IMAGE}' docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.production.yml up -d --no-build --remove-orphans ${compose_services} && docker image prune -f"

echo "Deployment finished for services: ${compose_services}"
