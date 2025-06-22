import os
import logging
from base64 import b64encode, b64decode
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidKey

from app.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """暗号化サービス"""

    def __init__(self):
        """暗号化サービスを初期化"""
        self._validate_security_settings()
        self.key = self._generate_key()
        self.fernet = Fernet(self.key)
        logger.info("EncryptionService initialized successfully")

    def _validate_security_settings(self) -> None:
        """セキュリティ設定の検証"""
        # 設定クラスでバリデーション済みだが、追加の検証
        if not settings.ENCRYPTION_KEY or not settings.ENCRYPTION_SALT:
            raise ValueError("ENCRYPTION_KEY and ENCRYPTION_SALT must be set")

        logger.info(f"Security settings validated: iterations={settings.ENCRYPTION_ITERATIONS}, "
                   f"key_length={settings.ENCRYPTION_KEY_LENGTH}, algorithm={settings.ENCRYPTION_ALGORITHM}")

    def _generate_key(self) -> bytes:
        """設定に基づいて暗号化キーを生成"""
        try:
            salt = settings.ENCRYPTION_SALT.encode()
            iterations = settings.ENCRYPTION_ITERATIONS
            key_length = settings.ENCRYPTION_KEY_LENGTH

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=key_length,
                salt=salt,
                iterations=iterations,
            )
            key = b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode()))
            logger.debug("Encryption key generated successfully")
            return key
        except Exception as e:
            logger.error(f"Failed to generate encryption key: {e}")
            raise

    def encrypt_data(self, data: str) -> bytes:
        """
        データを暗号化します。

        Args:
            data: 暗号化するデータ

        Returns:
            bytes: 暗号化されたデータ

        Raises:
            ValueError: データが空の場合
            Exception: 暗号化に失敗した場合
        """
        if not data:
            raise ValueError("Data cannot be empty")

        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            logger.debug("Data encrypted successfully")
            return encrypted_data
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise

    def decrypt_data(self, encrypted_data: bytes) -> str:
        """
        暗号化されたデータを復号化します。

        Args:
            encrypted_data: 復号化するデータ

        Returns:
            str: 復号化されたデータ

        Raises:
            ValueError: データが空の場合
            InvalidKey: 無効なキーの場合
            Exception: 復号化に失敗した場合
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")

        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            logger.debug("Data decrypted successfully")
            return decrypted_data.decode()
        except InvalidKey as e:
            logger.error(f"Invalid encryption key: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise

    def test_encryption(self) -> bool:
        """
        暗号化/復号化のテストを実行します。

        Returns:
            bool: テストが成功した場合True
        """
        try:
            test_data = "test_encryption_data"
            encrypted = self.encrypt_data(test_data)
            decrypted = self.decrypt_data(encrypted)
            success = decrypted == test_data
            logger.info(f"Encryption test {'passed' if success else 'failed'}")
            return success
        except Exception as e:
            logger.error(f"Encryption test failed: {e}")
            return False


# グローバルインスタンス（後方互換性のため）
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """暗号化サービスのインスタンスを取得します（シングルトン）"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


# 後方互換性のための関数
def encrypt_data(data: str) -> bytes:
    """データを暗号化します（後方互換性）"""
    return get_encryption_service().encrypt_data(data)


def decrypt_data(encrypted_data: bytes) -> str:
    """暗号化されたデータを復号化します（後方互換性）"""
    return get_encryption_service().decrypt_data(encrypted_data) 