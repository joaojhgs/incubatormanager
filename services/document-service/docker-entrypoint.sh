#!/bin/sh
set -e
cd /app
/usr/local/bin/minio-init.sh
python manage.py migrate --noinput
exec "$@"
