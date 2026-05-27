#!/usr/bin/env bash
# Run deterministic demo seed data on the remote production Docker host.
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
  if [[ -n "$registry_host_fallback" ]]; then
    registry_image="${registry_host_fallback}/${project_path}"
  fi
fi

image_tag="${IMAGE_TAG:-${CI_COMMIT_SHA:-latest}}"
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
remote_current="${DEPLOY_PATH}/current"

remote_env=("IMAGE_TAG=${image_tag}")
if [[ -n "$registry_image" ]]; then
  remote_env+=("CI_REGISTRY_IMAGE=${registry_image}")
fi

printf -v env_prefix '%q ' "${remote_env[@]}"
"${ssh_cmd[@]}" "$ssh_target" \
  "cd '${remote_current}' && ${env_prefix} docker compose --env-file .env -f infra/docker-compose.yml -f infra/docker-compose.production.yml exec -T auth-service python /app/infra/seed/seed.py"

echo "Remote seed finished."
