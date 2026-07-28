#!/bin/sh
set -e

echo "Running container database migrations via Alembic..."
alembic upgrade head

exec "$@"