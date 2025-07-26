"""
日次株価DTO

J-Quants APIから取得した日次株価データを表現するデータ転送オブジェクト
"""

from dataclasses import dataclass
from typing import Optional
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class DailyQuoteDTO:
    """
    日次株価DTO
    
    J-Quants APIのレスポンスをビジネスロジックで扱いやすい形式に変換
    """
    # 必須フィールド
    code: str  # 銘柄コード（5桁）
    date: date  # 日付
    
    # 価格データ（調整前）
    open: Optional[Decimal] = None  # 始値
    high: Optional[Decimal] = None  # 高値
    low: Optional[Decimal] = None  # 安値
    close: Optional[Decimal] = None  # 終値
    
    # 出来高・売買代金
    volume: Optional[int] = None  # 出来高
    turnover_value: Optional[Decimal] = None  # 売買代金
    
    # 調整係数
    adjustment_factor: Optional[Decimal] = None  # 調整係数
    
    # 調整後価格データ
    adjustment_open: Optional[Decimal] = None  # 調整後始値
    adjustment_high: Optional[Decimal] = None  # 調整後高値
    adjustment_low: Optional[Decimal] = None  # 調整後安値
    adjustment_close: Optional[Decimal] = None  # 調整後終値
    adjustment_volume: Optional[Decimal] = None  # 調整後出来高
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "code": self.code,
            "date": self.date.isoformat(),
            "open": float(self.open) if self.open is not None else None,
            "high": float(self.high) if self.high is not None else None,
            "low": float(self.low) if self.low is not None else None,
            "close": float(self.close) if self.close is not None else None,
            "volume": self.volume,
            "turnover_value": float(self.turnover_value) if self.turnover_value is not None else None,
            "adjustment_factor": float(self.adjustment_factor) if self.adjustment_factor is not None else None,
            "adjustment_open": float(self.adjustment_open) if self.adjustment_open is not None else None,
            "adjustment_high": float(self.adjustment_high) if self.adjustment_high is not None else None,
            "adjustment_low": float(self.adjustment_low) if self.adjustment_low is not None else None,
            "adjustment_close": float(self.adjustment_close) if self.adjustment_close is not None else None,
            "adjustment_volume": float(self.adjustment_volume) if self.adjustment_volume is not None else None,
        }
    
    @classmethod
    def from_api_response(cls, data: dict) -> "DailyQuoteDTO":
        """
        APIレスポンスからDTOを生成
        
        Args:
            data: J-Quants APIのレスポンスデータ
            
        Returns:
            DailyQuoteDTO: 変換されたDTO
        """
        # 日付の変換
        quote_date = date.fromisoformat(data["Date"])
        
        # 数値フィールドの安全な変換
        def to_decimal(value) -> Optional[Decimal]:
            if value is None:
                return None
            try:
                return Decimal(str(value))
            except (ValueError, TypeError):
                return None
        
        def to_int(value) -> Optional[int]:
            if value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        return cls(
            code=str(data.get("Code", "")),
            date=quote_date,
            open=to_decimal(data.get("Open")),
            high=to_decimal(data.get("High")),
            low=to_decimal(data.get("Low")),
            close=to_decimal(data.get("Close")),
            volume=to_int(data.get("Volume")),
            turnover_value=to_decimal(data.get("TurnoverValue")),
            adjustment_factor=to_decimal(data.get("AdjustmentFactor")),
            adjustment_open=to_decimal(data.get("AdjustmentOpen")),
            adjustment_high=to_decimal(data.get("AdjustmentHigh")),
            adjustment_low=to_decimal(data.get("AdjustmentLow")),
            adjustment_close=to_decimal(data.get("AdjustmentClose")),
            adjustment_volume=to_decimal(data.get("AdjustmentVolume")),
        )