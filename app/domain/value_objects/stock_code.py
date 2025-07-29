"""Stock code value object."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockCode:
    """銘柄コードのバリューオブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("銘柄コードは空にできません")
        
        # 銘柄コードの長さチェック（1-10 文字）- J-Quants API は様々な形式を返す可能性がある
        if len(self.value) > 10:
            raise ValueError("銘柄コードは 10 文字以下である必要があります")
        
        # 銘柄コードの形式チェック（英数字とハイフン、アンダースコアのみ）
        if not self.value.replace('-', '').replace('_', '').isalnum():
            raise ValueError("銘柄コードは英数字、ハイフン、アンダースコアのみ使用可能です")