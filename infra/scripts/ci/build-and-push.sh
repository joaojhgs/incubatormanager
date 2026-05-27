#!/usr/bin/env bash
# Build and push changed deployable images to the GitLab container registry.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=service-map.sh
source "$SCRIPT_DIR/service-map.sh"

: "${CI_REGISTRY_IMAGE:?CI_REGISTRY_IMAGE is required}"
: "${CI_COMMIT_SHA:?CI_COMMIT_SHA is required}"

image_tag="${IMAGE_TAG:-${CI_COMMIT_SHA}}"
services_string="${DEPLOY_IMAGES:-}"
if [[ -z "$services_string" ]]; then
  echo "No images to build."
  exit 0
fi

for svc in $services_string; do
  dockerfile="$(dockerfile_for "$svc")"
  image="${CI_REGISTRY_IMAGE}/${svc}:${image_tag}"
  latest="${CI_REGISTRY_IMAGE}/${svc}:${CI_COMMIT_REF_SLUG:-latest}"
  echo "Building ${image} from ${dockerfile}"
  docker build --pull -f "$dockerfile" -t "$image" -t "$latest" .
  docker push "$image"
  docker push "$latest"
done
