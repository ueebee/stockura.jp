.PHONY: help build up down logs test clean migrate shell docs run-script test-script test-scripts test-scripts-all test-scripts-all-auto

# Default target
help:
	@echo "Available commands:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start development environment"
	@echo "  make down        - Stop all containers"
	@echo "  make logs        - View container logs"
	@echo "  make test        - Run tests in Docker"
	@echo "  make clean       - Clean up containers and volumes"
	@echo "  make migrate     - Run database migrations (see 'make migrate' for options)"
	@echo "  make shell       - Open shell in app container"
	@echo "  make prod-build  - Build production images"
	@echo "  make prod-up     - Start production environment"
	@echo ""
	@echo "Script execution commands:"
	@echo "  make run-script SCRIPT=<name>    - Run any script in scripts/"
	@echo "  make test-script <name>          - Run a specific test script"
	@echo "  make test-scripts                - List available test scripts"
	@echo "  make test-scripts-all            - Run all test scripts"
	@echo "  make test-scripts-all-auto       - Run all test scripts with default choices"

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
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Usage: make migrate [command] [options]"; \
		echo "Commands:"; \
		echo "  upgrade [revision]  - Upgrade database (default: head)"; \
		echo "  downgrade revision  - Downgrade database"; \
		echo "  current            - Show current revision"; \
		echo "  history            - Show migration history"; \
		echo "  pending            - Check pending migrations"; \
		echo "  create             - Create new migration"; \
		echo "  init               - Initialize database"; \
		echo "  reset              - Reset database (CAUTION!)"; \
		docker-compose exec app python scripts/db_migrate.py --help; \
	else \
		docker-compose exec app python scripts/db_migrate.py $(filter-out $@,$(MAKECMDGOALS)); \
	fi

# Prevent make from treating migration commands as targets
%:
	@:

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

# Run scripts in Docker
run-script:
	@if [ -z "$(SCRIPT)" ]; then \
		echo "Usage: make run-script SCRIPT=<script_name>"; \
		echo "Example: make run-script SCRIPT=test_weekly_margin_interest.py"; \
		echo ""; \
		echo "Available scripts:"; \
		ls scripts/*.py | grep -v __pycache__ | grep -v __init__ | sed 's/scripts\///g'; \
	else \
		docker-compose exec app python scripts/$(SCRIPT); \
	fi

# Run test scripts
test-script:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Usage: make test-script [script_name]"; \
		echo "Available test scripts:"; \
		ls scripts/test_*.py | sed 's/scripts\///g'; \
	else \
		docker-compose exec app python scripts/$(filter-out $@,$(MAKECMDGOALS)); \
	fi

# Interactive test script selector
test-scripts:
	@echo "Available test scripts:"
	@echo "======================"
	@ls scripts/test_*.py | sed 's/scripts\///g' | nl -v 1
	@echo ""
	@echo "Run with: make test-script <script_name>"
	@echo "Example: make test-script test_weekly_margin_interest.py"

# Run all test scripts
test-scripts-all:
	@echo "Running all test scripts..."
	@for script in scripts/test_*.py; do \
		if [ -f "$$script" ]; then \
			echo ""; \
			echo "========================================"; \
			echo "Running: $$script"; \
			echo "========================================"; \
			docker-compose exec app python $$script || true; \
		fi; \
	done

# Run all test scripts with default choices
test-scripts-all-auto:
	@echo "Running all test scripts with default choices..."
	@for script in scripts/test_*.py; do \
		if [ -f "$$script" ]; then \
			echo ""; \
			echo "========================================"; \
			echo "Running: $$script (auto mode)"; \
			echo "========================================"; \
			if [ "$$(basename $$script)" = "test_api_listed_info.py" ]; then \
				docker-compose exec -e DEFAULT_CHOICES="1" app python $$script || true; \
			elif [ "$$(basename $$script)" = "test_announcement.py" ]; then \
				docker-compose exec -e DEFAULT_CHOICES="5" app python $$script || true; \
			elif [ "$$(basename $$script)" = "test_listed_info_task.py" ]; then \
				docker-compose exec -e DEFAULT_CHOICES="1" app python $$script || true; \
			else \
				docker-compose exec app python $$script || true; \
			fi; \
		fi; \
	done

# Cleanup
clean:
	docker-compose down -v
	docker-compose -f docker-compose.test.yml down -v
	docker system prune -f

clean-all:
	docker-compose down -v --rmi all
	docker-compose -f docker-compose.test.yml down -v --rmi all
	docker system prune -af --volumes