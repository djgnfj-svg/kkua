#!/bin/bash
# DB가 완전히 준비될 때까지 대기하는 스크립트

set -e

echo "Waiting for PostgreSQL to be ready..."

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up and running!"

# Redis 확인
echo "Waiting for Redis to be ready..."
until redis-cli -h redis ping 2>/dev/null; do
  echo "Redis is unavailable - sleeping"
  sleep 2
done

echo "Redis is up and running!"

echo "Starting backend application..."
exec "$@"