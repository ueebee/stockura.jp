from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from sqlalchemy import Column, String, Boolean, Integer, DateTime, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.services.encryption import encrypt_data, decrypt_data
from app.services.auth import StrategyRegistry


class DataSource(Base):
    """データソースのモデル"""

    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provider_type: Mapped[str] = mapped_column(String, nullable=False, index=True)  # "jquants", "yfinance" など
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String, nullable=False)
    api_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    rate_limit_per_day: Mapped[int] = mapped_column(Integer, default=86400, nullable=False)
    encrypted_credentials: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def set_credentials(self, credentials: Dict[str, Any]) -> None:
        """認証情報を暗号化して保存します。"""
        if credentials is None:
            self.encrypted_credentials = None
            return

        import json
        json_data = json.dumps(credentials)
        self.encrypted_credentials = encrypt_data(json_data)

    def get_credentials(self) -> Optional[Dict[str, Any]]:
        """暗号化された認証情報を復号化して返します。"""
        if self.encrypted_credentials is None:
            return None

        import json
        decrypted_data = decrypt_data(self.encrypted_credentials)
        return json.loads(decrypted_data)

    def get_refresh_token(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        リフレッシュトークンを取得します。

        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (成功フラグ, レスポンスデータ)
        """
        try:
            # 認証情報を取得
            credentials = self.get_credentials()
            if not credentials:
                return False, {"error": "No credentials found"}

            # 認証ストラテジーを取得
            strategy_class = StrategyRegistry.get_strategy(self.provider_type)
            if not strategy_class:
                return False, {"error": f"Unsupported provider type: {self.provider_type}"}

            # ストラテジーインスタンスを作成
            strategy = strategy_class(base_url=self.base_url)

            # リフレッシュトークンを取得
            token, expired_at = strategy.get_refresh_token(credentials)
            if not token or not expired_at:
                return False, {"error": "Failed to get refresh token"}

            return True, {
                "refresh_token": token,
                "expired_at": expired_at.isoformat()
            }

        except Exception as e:
            return False, {"error": str(e)}

    def get_id_token(self, refresh_token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        IDトークンを取得します。

        Args:
            refresh_token: リフレッシュトークン

        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (成功フラグ, レスポンスデータ)
        """
        try:
            # 認証ストラテジーを取得
            strategy_class = StrategyRegistry.get_strategy(self.provider_type)
            if not strategy_class:
                return False, {"error": f"Unsupported provider type: {self.provider_type}"}

            # ストラテジーインスタンスを作成
            strategy = strategy_class(base_url=self.base_url)

            # IDトークンを取得
            token, expired_at = strategy.get_id_token(refresh_token)
            if not token or not expired_at:
                return False, {"error": "Failed to get ID token"}

            return True, {
                "id_token": token,
                "expired_at": expired_at.isoformat()
            }

        except Exception as e:
            return False, {"error": str(e)} 