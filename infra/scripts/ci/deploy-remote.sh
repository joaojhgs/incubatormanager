#!/usr/bin/env bash
# Deploy changed images to a remote Docker host through SSH and Docker Compose.
set -euo pipefail

: "${DEPLOY_HOST:?Set DEPLOY_HOST as a protected GitLab CI variable}"
DEPLOY_USER="${DEPLOY_USER:-a69603}"
: "${DEPLOY_PATH:?Set DEPLOY_PATH or keep the CI default}"
: "${DEPLOY_PASSWORD:?Set DEPLOY_PASSWORD as a protected GitLab CI variable}"
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
ssh_opts=(-o ConnectTimeout=20 -o PreferredAuthentications=password -o PubkeyAuthentication=no)
mkdir -p ~/.ssh
chmod 700 ~/.ssh
export SSHPASS="$DEPLOY_PASSWORD"
if [[ -n "${DEPLOY_KNOWN_HOSTS:-}" ]]; then
  printf '%s\n' "$DEPLOY_KNOWN_HOSTS" > ~/.ssh/known_hosts
  chmod 600 ~/.ssh/known_hosts
else
  ssh_opts+=(-o StrictHostKeyChecking=accept-new)
fi
ssh_cmd=(sshpass -e ssh "${ssh_opts[@]}")
remote_release="${DEPLOY_PATH}/releases/${image_tag}"
remote_current="${DEPLOY_PATH}/current"

echo "Preparing remote release ${remote_release}"
"${ssh_cmd[@]}" "$ssh_target" "mkdir -p '${remote_release}' '${DEPLOY_PATH}/shared'"

tar \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/.next' \
  -czf - \
  .env.example infra gateway docker-compose.tilt.yml Tiltfile README.md docs \
  | "${ssh_cmd[@]}" "$ssh_target" "tar -xzf - -C '${remote_release}'"

if [[ -n "${DEPLOY_ENV_FILE_BASE64:-}" ]]; then
  printf '%s' "$DEPLOY_ENV_FILE_BASE64" | base64 -d | "${ssh_cmd[@]}" "$ssh_target" "cat > '${DEPLOY_PATH}/shared/.env'"
elif [[ -n "${DEPLOY_ENV_FILE:-}" ]]; then
  printf '%s\n' "$DEPLOY_ENV_FILE" | "${ssh_cmd[@]}" "$ssh_target" "cat > '${DEPLOY_PATH}/shared/.env'"
else
  "${ssh_cmd[@]}" "$ssh_target" \
    "test -f '${DEPLOY_PATH}/shared/.env' || cp '${remote_release}/.env.example' '${DEPLOY_PATH}/shared/.env'"
fi

registry_password_escaped="$(printf '%s' "$CI_REGISTRY_PASSWORD" | sed "s/'/'\\''/g")"
"${ssh_cmd[@]}" "$ssh_target" "docker login '${CI_REGISTRY}' -u '${CI_REGISTRY_USER}' -p '${registry_password_escaped}'"

"${ssh_cmd[@]}" "$ssh_target" \
  "ln -sfn '${remote_release}' '${remote_current}' && cd '${remote_current}' && ln -sfn '${DEPLOY_PATH}/shared/.env' .env && IMAGE_TAG='${image_tag}' CI_REGISTRY_IMAGE='${CI_REGISTRY_IMAGE}' docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.production.yml pull ${compose_services} && IMAGE_TAG='${image_tag}' CI_REGISTRY_IMAGE='${CI_REGISTRY_IMAGE}' docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.production.yml up -d --no-build --remove-orphans ${compose_services} && docker image prune -f"

echo "Deployment finished for services: ${compose_services}"
