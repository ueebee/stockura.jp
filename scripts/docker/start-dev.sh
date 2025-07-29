#!/bin/bash
# Development environment startup script

set -e

echo "Starting Stockura development environment with Docker..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.docker..."
    cp .env.docker .env
fi

# Stop any running containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Build images
echo "Building Docker images..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

# Start services
echo "Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Show logs
echo "Services started successfully!"
echo ""
echo "Services running at:"
echo "  - FastAPI app: http://localhost:8000"
echo "  - API docs: http://localhost:8000/docs"
echo "  - Flower (Celery monitoring): http://localhost:5555"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "To view logs: docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f"
echo "To stop: docker-compose -f docker-compose.yml -f docker-compose.dev.yml down"