#!/usr/bin/env bash
# Build and push changed deployable images to the GitLab container registry.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=service-map.sh
source "$SCRIPT_DIR/service-map.sh"

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
: "${CI_COMMIT_SHA:?CI_COMMIT_SHA is required}"

image_tag="${IMAGE_TAG:-${CI_COMMIT_SHA}}"
services_string="${DEPLOY_IMAGES:-}"
if [[ -z "$services_string" ]]; then
  echo "No images to build."
  exit 0
fi

registry_user="${CI_REGISTRY_USER:-gitlab-ci-token}"
registry_password="${CI_REGISTRY_PASSWORD:-${CI_JOB_TOKEN:-}}"
if [[ -z "$registry_password" ]]; then
  echo "No registry password is available; set CI_REGISTRY_PASSWORD or provide CI_JOB_TOKEN." >&2
  exit 2
fi
registry_host="${CI_REGISTRY:-${registry_image%%/*}}"
echo "$registry_password" | docker login "$registry_host" -u "$registry_user" --password-stdin
require_registry_push="${CI_REQUIRE_REGISTRY_PUSH:-false}"
skip_remaining_pushes="${CI_SKIP_REMAINING_PUSHES_AFTER_FAILURE:-true}"
push_failed=0

for svc in $services_string; do
  dockerfile="$(dockerfile_for "$svc")"
  image="${registry_image}/${svc}:${image_tag}"
  latest="${registry_image}/${svc}:${CI_COMMIT_REF_SLUG:-latest}"
  echo "Building ${image} from ${dockerfile}"
  docker build --pull -f "$dockerfile" -t "$image" -t "$latest" .
  if [[ "$push_failed" == "1" && "$skip_remaining_pushes" == "true" ]]; then
    echo "Skipping registry push for ${image} after an earlier push failure; remote deploy can still build on the target host." >&2
    continue
  fi
  if ! docker push "$image"; then
    echo "WARNING: could not push ${image}; remote deploy can still build on the target host." >&2
    push_failed=1
    continue
  fi
  if ! docker push "$latest"; then
    echo "WARNING: could not push ${latest}; remote deploy can still build on the target host." >&2
    push_failed=1
  fi
done

if [[ "$push_failed" == "1" && "$require_registry_push" == "true" ]]; then
  echo "At least one registry push failed and CI_REQUIRE_REGISTRY_PUSH=true." >&2
  exit 1
fi
