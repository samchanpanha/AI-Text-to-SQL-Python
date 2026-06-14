#!/bin/bash
set -e

echo "Waiting for MySQL..."
until mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; do
  sleep 2
done
echo "MySQL is ready."

echo "Running database initialization..."
python -m scripts.init_db 2>/dev/null || echo "Init script skipped or tables already exist."

echo "Starting application..."
exec "$@"
