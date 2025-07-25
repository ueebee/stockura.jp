"""
フィーチャーフラグ管理

段階的なリリースやA/Bテストのためのフィーチャーフラグ
"""

import os
from typing import Dict, Any


class FeatureFlags:
    """フィーチャーフラグの管理クラス"""
    
    # デフォルトのフラグ設定
    _default_flags = {
        "use_company_sync_service_v2": False,  # 新しいCompanySyncServiceを使用するか
        "enable_bulk_operations": True,         # バルク操作を有効にするか
        "enable_async_tasks": True,             # 非同期タスクを有効にするか
    }
    
    @classmethod
    def is_enabled(cls, flag_name: str) -> bool:
        """
        フィーチャーフラグが有効かどうかを確認
        
        Args:
            flag_name: フラグ名
            
        Returns:
            bool: 有効な場合True
        """
        # 環境変数から読み取り（FEATURE_FLAG_プレフィックス）
        env_key = f"FEATURE_FLAG_{flag_name.upper()}"
        env_value = os.getenv(env_key)
        
        if env_value is not None:
            return env_value.lower() in ("true", "1", "yes", "on")
        
        # デフォルト値を返す
        return cls._default_flags.get(flag_name, False)
    
    @classmethod
    def get_all_flags(cls) -> Dict[str, bool]:
        """
        全てのフィーチャーフラグの状態を取得
        
        Returns:
            Dict[str, bool]: フラグ名と状態のマップ
        """
        flags = {}
        for flag_name in cls._default_flags:
            flags[flag_name] = cls.is_enabled(flag_name)
        return flags
    
    @classmethod
    def set_flag(cls, flag_name: str, enabled: bool) -> None:
        """
        フィーチャーフラグを設定（テスト用）
        
        Args:
            flag_name: フラグ名
            enabled: 有効/無効
        """
        env_key = f"FEATURE_FLAG_{flag_name.upper()}"
        os.environ[env_key] = "true" if enabled else "false"