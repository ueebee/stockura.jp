"""テスト用のモックヘルパー関数"""
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import Any, List, Optional


class AsyncMockHelpers:
    """非同期処理用のモックヘルパークラス"""

    @staticmethod
    def create_aiohttp_mock_response(status_code: int, json_data: dict) -> AsyncMock:
        """aiohttp のレスポンスモックを作成"""
        mock_response = AsyncMock()
        mock_response.status = status_code
        mock_response.json = AsyncMock(return_value=json_data)
        return mock_response

    @staticmethod
    def create_aiohttp_session_mock() -> AsyncMock:
        """aiohttp のセッションモックを作成"""
        mock_session = AsyncMock()
        # close メソッドを追加
        mock_session.close = AsyncMock()
        return mock_session

    @staticmethod
    def setup_aiohttp_session_mock(
        mock_session_class: MagicMock,
        status_code: int,
        json_data: dict
    ) -> MagicMock:
        """aiohttp のセッションモックを完全にセットアップ"""
        # レスポンスのモック
        mock_response = AsyncMock()
        mock_response.status = status_code
        mock_response.json = AsyncMock(return_value=json_data)
        
        # コンテキストマネージャーのモック
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # セッションのモックを作成
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_context)
        mock_session.close = AsyncMock()
        
        # ClientSession のコンストラクタを設定
        mock_session_class.return_value = mock_session
        
        return mock_session


def create_mock_db_session():
    """SQLAlchemy のデータベースセッションモックを作成"""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.get = AsyncMock()
    mock_session.delete = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.scalars = AsyncMock()
    mock_session.scalar = AsyncMock()
    return mock_session


def create_mock_redis_client():
    """Redis クライアントのモックを作成"""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.setex = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.exists = AsyncMock()
    mock_redis.expire = AsyncMock()
    return mock_redis


class MockRepositoryHelpers:
    """リポジトリのモックヘルパークラス"""
    
    @staticmethod
    def create_mock_schedule_repository():
        """スケジュールリポジトリのモックを作成"""
        mock_repo = AsyncMock()
        mock_repo.create = AsyncMock()
        mock_repo.get_by_id = AsyncMock()
        mock_repo.get_by_name = AsyncMock()
        mock_repo.get_all = AsyncMock()
        mock_repo.update = AsyncMock()
        mock_repo.delete = AsyncMock()
        mock_repo.enable = AsyncMock()
        mock_repo.disable = AsyncMock()
        return mock_repo
    
    @staticmethod
    def create_mock_task_log_repository():
        """タスクログリポジトリのモックを作成"""
        mock_repo = AsyncMock()
        mock_repo.create = AsyncMock()
        mock_repo.get_by_id = AsyncMock()
        mock_repo.get_by_task_id = AsyncMock()
        mock_repo.get_by_schedule_id = AsyncMock()
        mock_repo.get_recent_logs = AsyncMock()
        mock_repo.update_status = AsyncMock()
        return mock_repo