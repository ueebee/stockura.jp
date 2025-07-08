.PHONY: test test-unit test-integration test-e2e coverage test-fast test-failed clean-test

# テスト用環境変数
export DATABASE_URL := postgresql+asyncpg://postgres:postgres@localhost:5432/stockura_test

# 全テスト実行
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

# テストデータベースのセットアップ
setup-test-db:
	docker exec stockurajp-db-1 psql -U postgres -c "DROP DATABASE IF EXISTS stockura_test;"
	docker exec stockurajp-db-1 psql -U postgres -c "CREATE DATABASE stockura_test;"
	@echo "Test database created successfully"

# ヘルプ
help:
	@echo "Available targets:"
	@echo "  make test              - Run all tests"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-e2e         - Run E2E tests only"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make test-fast        - Run tests excluding slow ones"
	@echo "  make test-failed      - Run only previously failed tests"
	@echo "  make clean-test       - Clean test artifacts"
	@echo "  make test-file FILE=  - Run specific test file"
	@echo "  make test-debug       - Run tests in debug mode"
	@echo "  make test-performance - Run performance tests"
	@echo "  make setup-test-db    - Setup test database"