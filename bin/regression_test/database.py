"""
データベース管理モジュール
現在はDockerコンテナの完全リセット方式を実装
"""
import subprocess
import time
from typing import Optional

from .config import TestConfig
from .utils import setup_logger


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, config: TestConfig):
        """
        Args:
            config: テスト設定
        """
        self.config = config
        self.logger = setup_logger(self.__class__.__name__, config.log_level, config.log_file)
        self.compose_cmd = f"docker compose -f {config.docker_compose_file}"
        
    def run_command(self, command: str, description: str = "", retry_count: Optional[int] = None) -> bool:
        """コマンドを実行し、成功/失敗を返す（リトライ機能付き）
        
        Args:
            command: 実行するコマンド
            description: コマンドの説明
            retry_count: リトライ回数（Noneの場合は設定値を使用）
            
        Returns:
            成功時True、失敗時False
        """
        if retry_count is None:
            retry_count = self.config.retry_count
            
        self.logger.info(f"実行: {description or command}")
        
        for attempt in range(retry_count):
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True
                )
                if result.stdout:
                    self.logger.debug(f"出力: {result.stdout.strip()}")
                return True
            except subprocess.CalledProcessError as e:
                self.logger.error(f"エラー (試行 {attempt + 1}/{retry_count}): {e.stderr}")
                if attempt < retry_count - 1:
                    self.logger.info(f"{self.config.retry_delay}秒後にリトライします...")
                    time.sleep(self.config.retry_delay)
                else:
                    return False
        return False
    
    def reset_database(self) -> bool:
        """データベースをクリーンな状態にリセット
        
        1. Docker環境を停止
        2. PostgreSQLボリュームを削除
        3. Docker環境を起動
        4. サービスの起動を待機
        5. マイグレーションを実行
        6. Docker環境を再起動（クリーンな状態を確保）
        
        Returns:
            成功時True、失敗時False
        """
        self.logger.info("="*60)
        self.logger.info("データベースのリセットを開始します")
        self.logger.info("="*60)
        
        commands = [
            (f"{self.compose_cmd} down", "Docker環境を停止"),
            ("docker volume rm stockurajp_postgres_data", "PostgreSQLボリュームを削除"),
            (f"{self.compose_cmd} up -d", "Docker環境を起動"),
            ("sleep 10", "サービスの起動を待機"),
            (f"{self.compose_cmd} exec -T web alembic upgrade head", "マイグレーションを実行"),
            (f"{self.compose_cmd} down", "Docker環境を一旦停止"),
            (f"{self.compose_cmd} up -d", "Docker環境を再起動"),
            ("sleep 15", "全サービスの起動を待機")
        ]
        
        for command, description in commands:
            if not self.run_command(command, description):
                # ボリューム削除でエラーが出る場合は無視（既に削除されている場合）
                if "docker volume rm" in command:
                    self.logger.info("ボリュームが既に削除されています（問題ありません）")
                    continue
                else:
                    self.logger.error(f"コマンド '{command}' の実行に失敗しました")
                    return False
        
        self.logger.info("データベースのリセットが完了しました")
        return True
    
    def wait_for_services(self, timeout: int = 60) -> bool:
        """サービスの起動を待機
        
        Args:
            timeout: タイムアウト時間（秒）
            
        Returns:
            サービスが起動した場合True、タイムアウトした場合False
        """
        self.logger.info(f"サービスの起動を待機しています（最大{timeout}秒）...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # webサービスのヘルスチェック
            check_cmd = f"{self.compose_cmd} exec -T web curl -s http://localhost:8000/health || true"
            try:
                result = subprocess.run(
                    check_cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if "ok" in result.stdout.lower() or "healthy" in result.stdout.lower():
                    self.logger.info("サービスが正常に起動しました")
                    return True
            except Exception as e:
                self.logger.debug(f"ヘルスチェックエラー: {e}")
            
            time.sleep(2)
        
        self.logger.error("サービスの起動がタイムアウトしました")
        return False
    
    def is_running(self) -> bool:
        """Docker環境が実行中かチェック
        
        Returns:
            実行中の場合True
        """
        check_cmd = f"{self.compose_cmd} ps --services --filter 'status=running'"
        try:
            result = subprocess.run(
                check_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            running_services = result.stdout.strip().split('\n')
            # webとdbサービスが実行中か確認
            return 'web' in running_services and 'db' in running_services
        except subprocess.CalledProcessError:
            return False