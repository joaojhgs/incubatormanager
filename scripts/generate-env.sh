#!/usr/bin/env bash
# generate-env.sh — Generate a .env file from .env.example with random secrets.
#
# Usage:
#   ./scripts/generate-env.sh          # create .env (prompts before overwriting)
#   ./scripts/generate-env.sh -f       # overwrite .env without prompting
#   ./scripts/generate-env.sh -o PATH  # write to a custom file instead of .env
#
# The script reads .env.example from the repository root, replaces every
# placeholder value that contains "change-me" or "dev" with a random secret,
# and writes the result to .env (or the file given with -o).
# Lines that are comments or blank are preserved as-is.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="${REPO_ROOT}/.env.example"
FORCE=false
OUTPUT="${REPO_ROOT}/.env"

usage() {
    echo "Usage: $0 [-f] [-o OUTPUT]"
    echo ""
    echo "  -f  Overwrite OUTPUT without prompting"
    echo "  -o  Write to OUTPUT instead of .env (default: .env)"
    exit 1
}

while getopts "fo:h" opt; do
    case "$opt" in
        f) FORCE=true ;;
        o) OUTPUT="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

if [ ! -f "$EXAMPLE" ]; then
    echo "ERROR: .env.example not found at ${EXAMPLE}" >&2
    exit 1
fi

if [ -f "$OUTPUT" ] && [ "$FORCE" = false ]; then
    read -rp "${OUTPUT} already exists. Overwrite? [y/N] " answer
    case "$answer" in
        [yY]*) ;;
        *) echo "Aborted."; exit 0 ;;
    esac
fi

# Generate a random hex string (32 bytes = 64 hex chars by default).
# Falls back to /dev/urandom if openssl is unavailable.
random_hex() {
    local len="${1:-32}"
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex "$len"
    else
        head -c "$((len * 2))" /dev/urandom | xxd -p -c "$((len * 2))" | head -c "$((len * 2))"
    fi
}

# Generate a random alphanumeric password (no special chars for DB compat).
random_password() {
    local len="${1:-24}"
    tr -dc 'A-Za-z0-9' </dev/urandom | head -c "$len"
}

process_line() {
    local line="$1"

    # Preserve comments and blank lines
    if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// /}" ]]; then
        echo "$line"
        return
    fi

    local key value
    key="${line%%=*}"
    value="${line#*=}"

    # Skip lines without = (shouldn't happen in well-formed .env)
    if [ "$key" = "$line" ]; then
        echo "$line"
        return
    fi

    case "$key" in
        # PostgreSQL superuser password
        POSTGRES_PASSWORD)
            echo "${key}=$(random_password 32)"
            ;;
        # Per-service DB passwords
        AUTH_DB_PASSWORD|COMPANY_DB_PASSWORD|CONTRACT_DB_PASSWORD|\
        FINANCE_DB_PASSWORD|SPACE_DB_PASSWORD|BOOKING_DB_PASSWORD|\
        INVENTORY_DB_PASSWORD|TICKET_DB_PASSWORD|DASHBOARD_DB_PASSWORD|\
        DOCUMENT_DB_PASSWORD)
            echo "${key}=$(random_password 24)"
            ;;
        # Django secret key
        DJANGO_SECRET_KEY)
            echo "${key}=$(random_hex 50)"
            ;;
        # JWT signing key (optional but we generate one)
        AUTH_JWT_SECRET)
            echo "${key}=$(random_hex 32)"
            ;;
        # MinIO credentials
        MINIO_ROOT_USER)
            echo "${key}=minioadmin"
            ;;
        MINIO_ROOT_PASSWORD)
            echo "${key}=$(random_password 32)"
            ;;
        # Frontend — keep default for local dev
        NEXT_PUBLIC_API_URL)
            echo "${key}=http://localhost/api"
            ;;
        # Any other key that contains "change-me" or "dev" placeholder
        *)
            if [[ "$value" == *"change-me"* ]] || [[ "$value" == *"dev"* && "$value" != *"amqp"* && "$value" != *"redis"* ]]; then
                echo "${key}=$(random_password 24)"
            else
                echo "$line"
            fi
            ;;
    esac
}

echo "Generating ${OUTPUT} from ${EXAMPLE} ..."

{
    while IFS= read -r line || [ -n "$line" ]; do
        process_line "$line"
    done < "$EXAMPLE"
} > "$OUTPUT"

echo "Done. Review ${OUTPUT} and adjust any values as needed."
