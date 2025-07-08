.PHONY: test test-unit test-integration test-e2e coverage test-fast test-failed clean-test test-docker test-docker-build

# テスト用環境変数（ローカル環境でテストする場合）
export DATABASE_URL := postgresql+asyncpg://postgres:postgres@localhost:5433/stockura_test
export REDIS_URL := redis://localhost:6380/1

# Docker環境でテスト実行（推奨）
test-docker:
	docker compose -f docker-compose.test.yml run --rm test

# Docker環境でテスト実行（詳細出力）
test-docker-verbose:
	docker compose -f docker-compose.test.yml run --rm test pytest -v

# Docker環境でカバレッジ付きテスト
test-docker-coverage:
	docker compose -f docker-compose.test.yml run --rm test pytest --cov=app --cov-report=html --cov-report=term

# Dockerテストイメージのビルド
test-docker-build:
	docker compose -f docker-compose.test.yml build test

# ローカル環境でテスト実行（Docker DBを使用）
test:
	./venv/bin/pytest

# 単体テストのみ実行
test-unit:
	./venv/bin/pytest tests/unit -v

# 統合テストのみ実行
test-integration:
	./venv/bin/pytest tests/integration -v -m integration

# E2Eテストのみ実行
test-e2e:
	./venv/bin/pytest tests/e2e -v -m e2e

# カバレッジ付きテスト実行
coverage:
	./venv/bin/pytest --cov=app --cov-report=html --cov-report=term --cov-fail-under=80

# 高速テスト（slowマーカーを除外）
test-fast:
	./venv/bin/pytest -m "not slow" -v

# 前回失敗したテストのみ実行
test-failed:
	./venv/bin/pytest --lf -v

# テストクリーンアップ
clean-test:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +

# 特定のテストを実行
test-file:
	@echo "Usage: make test-file FILE=tests/path/to/test_file.py"
	@test -n "$(FILE)" || (echo "Error: FILE is not set" && exit 1)
	./venv/bin/pytest $(FILE) -v

# デバッグモードでテスト実行
test-debug:
	./venv/bin/pytest -s -vv --tb=long

# パフォーマンステスト
test-performance:
	./venv/bin/pytest tests/performance -v -m performance

# 並列実行（pytest-xdistが必要）
test-parallel:
	./venv/bin/pytest -n auto

# テストデータベースのセットアップ（テスト用コンテナ）
setup-test-db:
	docker compose -f docker-compose.test.yml up -d db-test
	@sleep 3  # DBの起動を待つ
	docker compose -f docker-compose.test.yml exec db-test psql -U postgres -c "DROP DATABASE IF EXISTS stockura_test;"
	docker compose -f docker-compose.test.yml exec db-test psql -U postgres -c "CREATE DATABASE stockura_test;"
	@echo "Test database created successfully"

# テスト環境の起動
test-up:
	docker compose -f docker-compose.test.yml up -d db-test redis-test
	@echo "Test environment is up"

# テスト環境の停止
test-down:
	docker compose -f docker-compose.test.yml down
	@echo "Test environment is down"

# テスト環境の停止とボリューム削除
test-clean:
	docker compose -f docker-compose.test.yml down -v
	@echo "Test environment cleaned"

# ヘルプ
help:
	@echo "Available targets:"
	@echo ""
	@echo "Docker環境でのテスト実行（推奨）:"
	@echo "  make test-docker         - Run all tests in Docker"
	@echo "  make test-docker-verbose - Run tests with verbose output in Docker"
	@echo "  make test-docker-coverage- Run tests with coverage in Docker"
	@echo "  make test-docker-build   - Build test Docker image"
	@echo "  make test-up            - Start test environment (DB & Redis)"
	@echo "  make test-down          - Stop test environment"
	@echo "  make test-clean         - Stop and clean test environment"
	@echo ""
	@echo "ローカル環境でのテスト実行:"
	@echo "  make test               - Run all tests locally"
	@echo "  make test-unit          - Run unit tests only"
	@echo "  make test-integration   - Run integration tests only"
	@echo "  make test-e2e          - Run E2E tests only"
	@echo "  make coverage          - Run tests with coverage report"
	@echo "  make test-fast         - Run tests excluding slow ones"
	@echo "  make test-failed       - Run only previously failed tests"
	@echo "  make clean-test        - Clean test artifacts"
	@echo "  make test-file FILE=   - Run specific test file"
	@echo "  make test-debug        - Run tests in debug mode"
	@echo "  make test-performance  - Run performance tests"
	@echo "  make setup-test-db     - Setup test database"