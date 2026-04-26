#!/bin/sh
# Idempotent MinIO bucket provisioning (document storage).
# Reads MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_USE_SSL.

set -eu

bucket="${MINIO_BUCKET:-ilb-documents}"
endpoint="${MINIO_ENDPOINT:?MINIO_ENDPOINT is required}"
access="${MINIO_ACCESS_KEY:?MINIO_ACCESS_KEY is required}"
secret="${MINIO_SECRET_KEY:?MINIO_SECRET_KEY is required}"

use_ssl="${MINIO_USE_SSL:-false}"
case "$use_ssl" in
true | True | 1) scheme="https" ;;
*) scheme="http" ;;
esac

url="${scheme}://${endpoint}"
alias_name="ilb-bucket-init"

mc alias set "$alias_name" "$url" "$access" "$secret" >/dev/null

attempt=0
max_attempts=60
while [ "$attempt" -lt "$max_attempts" ]; do
  if mc mb --ignore-existing "${alias_name}/${bucket}"; then
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 2
done

echo "minio-init: failed to create bucket ${bucket} after ${max_attempts} attempts" >&2
exit 1
