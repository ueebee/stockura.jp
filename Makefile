.PHONY: help build up down logs test clean migrate shell docs

# Default target
help:
	@echo "Available commands:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start development environment"
	@echo "  make down        - Stop all containers"
	@echo "  make logs        - View container logs"
	@echo "  make test        - Run tests in Docker"
	@echo "  make clean       - Clean up containers and volumes"
	@echo "  make migrate     - Run database migrations"
	@echo "  make shell       - Open shell in app container"
	@echo "  make prod-build  - Build production images"
	@echo "  make prod-up     - Start production environment"

# Development commands
build:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

up:
	./scripts/docker/start-dev.sh

down:
	./scripts/docker/stop-all.sh

logs:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Testing
test:
	./scripts/docker/run-tests.sh

test-watch:
	docker-compose -f docker-compose.test.yml run --rm test-runner pytest -v --watch

# Database
migrate:
	docker-compose exec app python scripts/db_migrate.py

migrate-create:
	docker-compose exec app alembic revision -m "$(MSG)"

# Utilities
shell:
	docker-compose exec app bash

shell-db:
	docker-compose exec postgres psql -U stockura -d stockura

redis-cli:
	docker-compose exec redis redis-cli

# Production
prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

# Cleanup
clean:
	docker-compose down -v
	docker-compose -f docker-compose.test.yml down -v
	docker system prune -f

clean-all:
	docker-compose down -v --rmi all
	docker-compose -f docker-compose.test.yml down -v --rmi all
	docker system prune -af --volumes