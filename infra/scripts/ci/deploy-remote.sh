#!/usr/bin/env bash
# Deploy changed images to a remote Docker host through SSH and Docker Compose.
set -euo pipefail

: "${DEPLOY_HOST:?Set DEPLOY_HOST as a protected GitLab CI variable}"
DEPLOY_USER="${DEPLOY_USER:-a69603}"
: "${DEPLOY_PATH:?Set DEPLOY_PATH or keep the CI default}"
: "${DEPLOY_PASSWORD:?Set DEPLOY_PASSWORD as a protected GitLab CI variable}"
registry_image="${CI_REGISTRY_IMAGE:-}"
if [[ -z "$registry_image" ]]; then
  registry_host_fallback="${CI_REGISTRY:-${CI_SERVER_HOST:-}}"
  if [[ -z "$registry_host_fallback" && -n "${CI_SERVER_URL:-}" ]]; then
    registry_host_fallback="${CI_SERVER_URL#http://}"
    registry_host_fallback="${registry_host_fallback#https://}"
    registry_host_fallback="${registry_host_fallback%%/*}"
  fi
  project_path="${CI_PROJECT_PATH:-sdl/2025-2026/projects/sdl-project-group-20}"
  if [[ -z "$registry_host_fallback" ]]; then
    echo "CI_REGISTRY_IMAGE is missing and no CI_REGISTRY/CI_SERVER_HOST fallback is available." >&2
    exit 2
  fi
  registry_image="${registry_host_fallback}/${project_path}"
fi
registry_user="${CI_REGISTRY_USER:-gitlab-ci-token}"
registry_password="${CI_REGISTRY_PASSWORD:-${CI_JOB_TOKEN:-}}"
if [[ -z "$registry_password" ]]; then
  echo "No registry password is available; set CI_REGISTRY_PASSWORD or provide CI_JOB_TOKEN." >&2
  exit 2
fi

registry_host="${CI_REGISTRY:-${registry_image%%/*}}"
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

registry_password_escaped="$(printf '%s' "$registry_password" | sed "s/'/'\\''/g")"
registry_user_escaped="$(printf '%s' "$registry_user" | sed "s/'/'\\''/g")"
"${ssh_cmd[@]}" "$ssh_target" "docker login '${registry_host}' -u '${registry_user_escaped}' -p '${registry_password_escaped}'"

"${ssh_cmd[@]}" "$ssh_target" \
  "ln -sfn '${remote_release}' '${remote_current}' && cd '${remote_current}' && ln -sfn '${DEPLOY_PATH}/shared/.env' .env && IMAGE_TAG='${image_tag}' CI_REGISTRY_IMAGE='${registry_image}' docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.production.yml pull ${compose_services} && IMAGE_TAG='${image_tag}' CI_REGISTRY_IMAGE='${registry_image}' docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.production.yml up -d --no-build --remove-orphans ${compose_services} && docker image prune -f"

echo "Deployment finished for services: ${compose_services}"
