#!/bin/bash
# Test runner script for Docker environment

set -e

echo "Running tests in Docker environment..."

# Stop any existing test containers
echo "Cleaning up existing test containers..."
docker-compose -f docker-compose.test.yml down -v

# Build test image
echo "Building test image..."
docker-compose -f docker-compose.test.yml build test-runner

# Run tests
echo "Running tests..."
docker-compose -f docker-compose.test.yml run --rm test-runner

# Cleanup
echo "Cleaning up..."
docker-compose -f docker-compose.test.yml down -v

echo "Tests completed!"