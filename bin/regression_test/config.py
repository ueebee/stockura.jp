"""
リグレッションテスト設定管理モジュール
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TestConfig:
    """テスト設定を管理するデータクラス"""
    
    # 基本設定
    base_url: str = "http://localhost:8000"
    docker_compose_file: str = "docker-compose.yml"
    
    # タイムアウト設定
    test_timeout: int = 60  # 秒
    schedule_wait_minutes: int = 2  # 分
    
    # ブラウザ設定
    headless: bool = True
    
    # リトライ設定
    retry_count: int = 3
    retry_delay: int = 5  # 秒
    
    # 並列実行設定
    parallel_execution: bool = False
    max_parallel_workers: int = 4
    
    # ログ設定
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # テストデータ設定
    test_data_source: str = "clean"  # "clean" or "production"
    skip_db_reset: bool = False
    
    # レポート設定
    report_format: str = "json"  # "json" or "html"
    report_dir: str = "_tmp"
    
    # スクリーンショット設定
    screenshot_on_failure: bool = True
    screenshot_dir: str = "_tmp"
    
    @classmethod
    def from_env(cls) -> 'TestConfig':
        """環境変数から設定を読み込む"""
        return cls(
            base_url=os.getenv("STOCKURA_BASE_URL", cls.base_url),
            docker_compose_file=os.getenv("DOCKER_COMPOSE_FILE", cls.docker_compose_file),
            test_timeout=int(os.getenv("TEST_TIMEOUT", str(cls.test_timeout))),
            schedule_wait_minutes=int(os.getenv("SCHEDULE_WAIT_MINUTES", str(cls.schedule_wait_minutes))),
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            retry_count=int(os.getenv("RETRY_COUNT", str(cls.retry_count))),
            retry_delay=int(os.getenv("RETRY_DELAY", str(cls.retry_delay))),
            parallel_execution=os.getenv("PARALLEL_EXECUTION", "false").lower() == "true",
            max_parallel_workers=int(os.getenv("MAX_PARALLEL_WORKERS", str(cls.max_parallel_workers))),
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
            log_file=os.getenv("LOG_FILE"),
            test_data_source=os.getenv("TEST_DATA_SOURCE", cls.test_data_source),
            skip_db_reset=os.getenv("SKIP_DB_RESET", "false").lower() == "true",
            report_format=os.getenv("REPORT_FORMAT", cls.report_format),
            report_dir=os.getenv("REPORT_DIR", cls.report_dir),
            screenshot_on_failure=os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true",
            screenshot_dir=os.getenv("SCREENSHOT_DIR", cls.screenshot_dir),
        )
    
    def override_from_args(self, args) -> None:
        """コマンドライン引数で設定を上書き"""
        if hasattr(args, 'base_url') and args.base_url:
            self.base_url = args.base_url
        if hasattr(args, 'docker_compose_file') and args.docker_compose_file:
            self.docker_compose_file = args.docker_compose_file
        if hasattr(args, 'timeout') and args.timeout:
            self.test_timeout = args.timeout
        if hasattr(args, 'schedule_wait') and args.schedule_wait:
            self.schedule_wait_minutes = args.schedule_wait
        if hasattr(args, 'visible') and args.visible:
            self.headless = False
        if hasattr(args, 'retry_count') and args.retry_count:
            self.retry_count = args.retry_count
        if hasattr(args, 'skip_db_reset') and args.skip_db_reset:
            self.skip_db_reset = args.skip_db_reset
    
    def validate(self) -> None:
        """設定値の検証"""
        if self.test_timeout <= 0:
            raise ValueError("test_timeout must be positive")
        if self.schedule_wait_minutes <= 0:
            raise ValueError("schedule_wait_minutes must be positive")
        if self.retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        if self.max_parallel_workers <= 0:
            raise ValueError("max_parallel_workers must be positive")
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log_level: {self.log_level}")
        if self.report_format not in ["json", "html"]:
            raise ValueError(f"Invalid report_format: {self.report_format}")
        if self.test_data_source not in ["clean", "production"]:
            raise ValueError(f"Invalid test_data_source: {self.test_data_source}")