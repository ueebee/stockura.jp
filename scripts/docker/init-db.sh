#!/bin/bash
# Database initialization script

set -e

echo "Initializing database..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run migrations
echo "Running database migrations..."
docker-compose exec app python scripts/db_migrate.py

echo "Database initialization completed!"