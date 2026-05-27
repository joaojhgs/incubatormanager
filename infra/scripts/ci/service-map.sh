#!/usr/bin/env bash
# Shared service metadata for CI build and Docker Compose deployment.
set -euo pipefail

# Deployable image names built by this repository.
DEPLOYABLE_IMAGES=(
  auth-service
  company-service
  contract-service
  finance-service
  space-service
  booking-service
  inventory-service
  ticket-service
  dashboard-service
  document-service
  frontend
  gateway
)

# Dockerfile path by deployable image name.
dockerfile_for() {
  case "$1" in
    auth-service) echo "services/auth-service/Dockerfile" ;;
    company-service) echo "services/company-service/Dockerfile" ;;
    contract-service) echo "services/contract-service/Dockerfile" ;;
    finance-service) echo "services/finance-service/Dockerfile" ;;
    space-service) echo "services/space-service/Dockerfile" ;;
    booking-service) echo "services/booking-service/Dockerfile" ;;
    inventory-service) echo "services/inventory-service/Dockerfile" ;;
    ticket-service) echo "services/ticket-service/Dockerfile" ;;
    dashboard-service) echo "services/dashboard-service/Dockerfile" ;;
    document-service) echo "services/document-service/Dockerfile" ;;
    frontend) echo "frontend/Dockerfile" ;;
    gateway) echo "gateway/Dockerfile" ;;
    *) echo "Unknown deployable image: $1" >&2; return 2 ;;
  esac
}

# Compose services that must be restarted when a deployable image changes.
compose_services_for() {
  case "$1" in
    auth-service) echo "auth-service" ;;
    company-service) echo "company-service" ;;
    contract-service) echo "contract-service contract-scheduler" ;;
    finance-service) echo "finance-service finance-consumer finance-scheduler" ;;
    space-service) echo "space-service space-consumer" ;;
    booking-service) echo "booking-service booking-scheduler" ;;
    inventory-service) echo "inventory-service inventory-consumer" ;;
    ticket-service) echo "ticket-service" ;;
    dashboard-service) echo "dashboard-service dashboard-consumer" ;;
    document-service) echo "document-service" ;;
    frontend) echo "frontend" ;;
    gateway) echo "gateway" ;;
    *) echo "Unknown deployable image: $1" >&2; return 2 ;;
  esac
}

# Print a unique, ordered list from stdin/args.
unique_words() {
  awk 'BEGIN{RS="[[:space:]]+"} NF && !seen[$0]++ {print $0}' "$@" | tr '\n' ' ' | sed 's/[[:space:]]*$//'
}
