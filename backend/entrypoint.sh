#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until python -c "import psycopg2; psycopg2.connect('${DATABASE_URL:-postgresql://evvents:evvents@db:5432/evvents}')" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL ready"

echo "Waiting for Redis..."
until python -c "import redis; redis.Redis.from_url('${REDIS_URL:-redis://redis:6379/0}').ping()" 2>/dev/null; do
    sleep 1
done
echo "Redis ready"

echo "Running database migrations..."
flask db upgrade

echo "Starting application..."
exec "$@"
