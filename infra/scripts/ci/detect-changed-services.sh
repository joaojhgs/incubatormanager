#!/usr/bin/env bash
# Detect deployable images affected by the current commit range.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=service-map.sh
source "$SCRIPT_DIR/service-map.sh"

base_ref="${CI_MERGE_REQUEST_DIFF_BASE_SHA:-${CI_COMMIT_BEFORE_SHA:-}}"
head_ref="${CI_COMMIT_SHA:-HEAD}"

if [[ -z "${base_ref}" || "${base_ref}" =~ ^0+$ ]] || ! git cat-file -e "${base_ref}^{commit}" 2>/dev/null; then
  base_ref="$(git rev-list --max-parents=0 "$head_ref" | tail -n 1)"
fi

mapfile -t changed_files < <(git diff --name-only "$base_ref" "$head_ref")
if [[ ${#changed_files[@]} -eq 0 ]]; then
  mapfile -t changed_files < <(git show --format= --name-only "$head_ref" | sed '/^$/d')
fi

all=false
declare -A selected=()
for path in "${changed_files[@]}"; do
  [[ -z "$path" ]] && continue
  case "$path" in
    services/auth-service/*) selected[auth-service]=1 ;;
    services/company-service/*) selected[company-service]=1 ;;
    services/contract-service/*|infra/cron/contract.crontab) selected[contract-service]=1 ;;
    services/finance-service/*|infra/cron/finance.crontab) selected[finance-service]=1 ;;
    services/space-service/*) selected[space-service]=1 ;;
    services/booking-service/*|infra/cron/booking.crontab) selected[booking-service]=1 ;;
    services/inventory-service/*) selected[inventory-service]=1 ;;
    services/ticket-service/*) selected[ticket-service]=1 ;;
    services/dashboard-service/*) selected[dashboard-service]=1 ;;
    services/document-service/*) selected[document-service]=1 ;;
    frontend/*) selected[frontend]=1 ;;
    gateway/*) selected[gateway]=1 ;;
    libs/py-common/*|pyproject.toml) for svc in "${DEPLOYABLE_IMAGES[@]}"; do [[ "$svc" == frontend || "$svc" == gateway ]] || selected[$svc]=1; done ;;
    infra/docker-compose*.yml|infra/docker/*|infra/scripts/*|.env.example|.gitlab-ci.yml|.gitlab/ci/*) all=true ;;
  esac
done

if [[ "$all" == true ]]; then
  for svc in "${DEPLOYABLE_IMAGES[@]}"; do selected[$svc]=1; done
fi

services=()
for svc in "${DEPLOYABLE_IMAGES[@]}"; do
  [[ -n "${selected[$svc]:-}" ]] && services+=("$svc")
done

if [[ ${#services[@]} -eq 0 ]]; then
  echo "DEPLOY_IMAGES=" > changed-services.env
  echo "DEPLOY_COMPOSE_SERVICES=" >> changed-services.env
  echo "No deployable service changes detected."
  exit 0
fi

compose_services=()
for svc in "${services[@]}"; do
  read -r -a expanded <<< "$(compose_services_for "$svc")"
  compose_services+=("${expanded[@]}")
done

printf 'DEPLOY_IMAGES=%s\n' "${services[*]}" > changed-services.env
printf 'DEPLOY_COMPOSE_SERVICES=%s\n' "$(printf '%s\n' "${compose_services[@]}" | unique_words)" >> changed-services.env
cat changed-services.env
