"""
リグレッションテスト用ユーティリティモジュール
"""
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def setup_logger(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """ロガーをセットアップする
    
    Args:
        name: ロガー名
        level: ログレベル
        log_file: ログファイルパス（指定時はファイルにも出力）
    
    Returns:
        設定済みのロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # 既存のハンドラをクリア
    logger.handlers.clear()
    
    # フォーマッター
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラ（指定時）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_jst_time_after_minutes(minutes: int) -> str:
    """現在時刻から指定分後のJST時刻を HH:MM 形式で返す
    
    Args:
        minutes: 加算する分数
    
    Returns:
        HH:MM形式のJST時刻文字列
    """
    # 現在のJST時刻を取得（UTC+9）
    jst_offset = timedelta(hours=9)
    jst_now = datetime.utcnow() + jst_offset
    future_time = jst_now + timedelta(minutes=minutes)
    return future_time.strftime("%H:%M")


def get_jst_time_after_seconds(seconds: int) -> str:
    """現在時刻から指定秒後のJST時刻を HH:MM:SS 形式で返す
    
    Args:
        seconds: 加算する秒数
    
    Returns:
        HH:MM:SS形式のJST時刻文字列
    """
    # 現在のJST時刻を取得（UTC+9）
    jst_offset = timedelta(hours=9)
    jst_now = datetime.utcnow() + jst_offset
    future_time = jst_now + timedelta(seconds=seconds)
    return future_time.strftime("%H:%M:%S")


def ensure_dir(path: str) -> Path:
    """ディレクトリが存在しなければ作成する
    
    Args:
        path: ディレクトリパス
    
    Returns:
        Pathオブジェクト
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def format_duration(seconds: float) -> str:
    """秒数を人間が読みやすい形式に変換
    
    Args:
        seconds: 秒数
    
    Returns:
        フォーマット済み文字列（例: "1分23秒", "45.2秒"）
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}分{remaining_seconds:.0f}秒"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}時間{remaining_minutes}分"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """テキストを指定長で切り詰める
    
    Args:
        text: 対象テキスト
        max_length: 最大文字数
        suffix: 切り詰め時の接尾辞
    
    Returns:
        切り詰められたテキスト
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


class TestResult:
    """テスト結果を格納するクラス"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "PENDING"  # PENDING, RUNNING, SUCCESS, FAILED, SKIPPED
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.errors = []
        self.warnings = []
        self.details = {}
        
    def start(self):
        """テスト開始を記録"""
        self.status = "RUNNING"
        self.start_time = datetime.now()
        
    def success(self, **details):
        """テスト成功を記録"""
        self.status = "SUCCESS"
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.details.update(details)
        
    def fail(self, error: str, **details):
        """テスト失敗を記録"""
        self.status = "FAILED"
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.errors.append(error)
        self.details.update(details)
        
    def skip(self, reason: str):
        """テストスキップを記録"""
        self.status = "SKIPPED"
        self.details['skip_reason'] = reason
        
    def add_warning(self, warning: str):
        """警告を追加"""
        self.warnings.append(warning)
        
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details
        }