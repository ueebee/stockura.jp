from typing import Dict, Type, Optional
from .base import AuthStrategy


class StrategyRegistry:
    """認証ストラテジーのレジストリ"""

    _strategies: Dict[str, Type[AuthStrategy]] = {}

    @classmethod
    def register(cls, provider_type: str, strategy_class: Type[AuthStrategy]) -> None:
        """
        ストラテジーを登録します。

        Args:
            provider_type: プロバイダータイプ
            strategy_class: ストラテジークラス
        """
        cls._strategies[provider_type] = strategy_class

    @classmethod
    def get_strategy(cls, provider_type: str) -> Optional[Type[AuthStrategy]]:
        """
        プロバイダータイプに対応するストラテジーを取得します。

        Args:
            provider_type: プロバイダータイプ

        Returns:
            Optional[Type[AuthStrategy]]: ストラテジークラス
        """
        return cls._strategies.get(provider_type)

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """
        サポートされているプロバイダーのリストを取得します。

        Returns:
            list[str]: プロバイダータイプのリスト
        """
        return list(cls._strategies.keys()) 