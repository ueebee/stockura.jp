#!/bin/bash
# Stop all Docker containers

set -e

echo "Stopping all Stockura Docker containers..."

# Stop development environment
if docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps -q 2>/dev/null; then
    echo "Stopping development containers..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
fi

# Stop production environment
if docker-compose ps -q 2>/dev/null; then
    echo "Stopping production containers..."
    docker-compose down
fi

# Stop test environment
if docker-compose -f docker-compose.test.yml ps -q 2>/dev/null; then
    echo "Stopping test containers..."
    docker-compose -f docker-compose.test.yml down -v
fi

echo "All containers stopped!"