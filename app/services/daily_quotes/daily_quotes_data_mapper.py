"""
日次株価データマッパー実装

APIレスポンスのデータ検証と変換を担当
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.services.interfaces.daily_quotes_sync_interfaces import IDailyQuotesDataMapper
from app.core.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class DailyQuotesDataMapper(IDailyQuotesDataMapper):
    """日次株価データマッパー"""
    
    def map_to_model(self, api_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        APIデータをモデル用にマッピング
        
        Args:
            api_data: J-Quants APIレスポンスデータ
            
        Returns:
            Optional[Dict[str, Any]]: モデル用にマッピングされたデータ（無効な場合はNone）
        """
        # データ検証
        is_valid, error_msg = self.validate_quote_data(api_data)
        if not is_valid:
            logger.warning(f"Invalid quote data: {error_msg}")
            return None
        
        try:
            # 日付変換
            trade_date = datetime.strptime(api_data["Date"], "%Y-%m-%d").date()
            
            # マッピング
            mapped_data = {
                "code": api_data["Code"],
                "trade_date": trade_date,
                
                # 調整前価格データ
                "open_price": self.convert_price_fields(api_data.get("Open")),
                "high_price": self.convert_price_fields(api_data.get("High")),
                "low_price": self.convert_price_fields(api_data.get("Low")),
                "close_price": self.convert_price_fields(api_data.get("Close")),
                "volume": self.convert_volume_fields(api_data.get("Volume")),
                "turnover_value": self.convert_volume_fields(api_data.get("TurnoverValue")),
                
                # 調整後価格データ
                "adjustment_factor": self.convert_price_fields(api_data.get("AdjustmentFactor", 1.0)),
                "adjustment_open": self.convert_price_fields(api_data.get("AdjustmentOpen")),
                "adjustment_high": self.convert_price_fields(api_data.get("AdjustmentHigh")),
                "adjustment_low": self.convert_price_fields(api_data.get("AdjustmentLow")),
                "adjustment_close": self.convert_price_fields(api_data.get("AdjustmentClose")),
                "adjustment_volume": self.convert_volume_fields(api_data.get("AdjustmentVolume")),
                
                # 制限フラグ
                "upper_limit_flag": self._convert_bool(api_data.get("UpperLimit", False)),
                "lower_limit_flag": self._convert_bool(api_data.get("LowerLimit", False)),
                
                # Premium限定データ（前場・後場）
                "morning_open": self.convert_price_fields(api_data.get("MorningOpen")),
                "morning_high": self.convert_price_fields(api_data.get("MorningHigh")),
                "morning_low": self.convert_price_fields(api_data.get("MorningLow")),
                "morning_close": self.convert_price_fields(api_data.get("MorningClose")),
                "morning_volume": self.convert_volume_fields(api_data.get("MorningVolume")),
                "morning_turnover_value": self.convert_volume_fields(api_data.get("MorningTurnoverValue")),
                
                "afternoon_open": self.convert_price_fields(api_data.get("AfternoonOpen")),
                "afternoon_high": self.convert_price_fields(api_data.get("AfternoonHigh")),
                "afternoon_low": self.convert_price_fields(api_data.get("AfternoonLow")),
                "afternoon_close": self.convert_price_fields(api_data.get("AfternoonClose")),
                "afternoon_volume": self.convert_volume_fields(api_data.get("AfternoonVolume")),
                "afternoon_turnover_value": self.convert_volume_fields(api_data.get("AfternoonTurnoverValue")),
            }
            
            return mapped_data
            
        except Exception as e:
            logger.error(f"Error mapping quote data: {e}")
            return None
    
    def validate_quote_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        株価データの妥当性検証
        
        Args:
            data: 検証対象データ
            
        Returns:
            Tuple[bool, Optional[str]]: (検証結果, エラーメッセージ)
        """
        # 必須フィールドの確認
        required_fields = ["Code", "Date"]
        for field in required_fields:
            if field not in data or data[field] is None:
                return False, f"Missing required field: {field}"
        
        # 日付フォーマットの検証
        try:
            datetime.strptime(data["Date"], "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid date format: {data['Date']}"
        
        # 銘柄コードの検証
        if not isinstance(data["Code"], str) or len(data["Code"]) == 0:
            return False, "Invalid code format"
        
        # 四本値の論理的整合性チェック（データが存在する場合）
        ohlc_fields = ["Open", "High", "Low", "Close"]
        if all(field in data and data[field] is not None for field in ohlc_fields):
            try:
                open_price = float(data["Open"])
                high_price = float(data["High"])
                low_price = float(data["Low"])
                close_price = float(data["Close"])
                
                # 価格が負の値でないことを確認（最初にチェック）
                if any(price < 0 for price in [open_price, high_price, low_price, close_price]):
                    return False, "Negative price values detected"
                
                # 高値・安値の整合性チェック
                if not (low_price <= open_price <= high_price and 
                       low_price <= close_price <= high_price and
                       low_price <= high_price):
                    return False, f"Invalid OHLC relationship: O={open_price}, H={high_price}, L={low_price}, C={close_price}"
                    
            except (ValueError, TypeError):
                return False, "Invalid numeric values in OHLC data"
        
        return True, None
    
    def convert_price_fields(self, value: Any) -> Optional[Decimal]:
        """
        価格フィールドの安全な変換
        
        Args:
            value: 変換対象の値
            
        Returns:
            Optional[Decimal]: 変換された価格（変換できない場合はNone）
        """
        if value is None or value == "":
            return None
        
        try:
            decimal_value = Decimal(str(value))
            # 負の値チェック
            if decimal_value < 0:
                logger.warning(f"Negative price value detected: {value}")
                return None
            return decimal_value
        except (ValueError, TypeError, InvalidOperation) as e:
            logger.warning(f"Failed to convert price value '{value}': {e}")
            return None
    
    def convert_volume_fields(self, value: Any) -> Optional[int]:
        """
        出来高フィールドの安全な変換
        
        Args:
            value: 変換対象の値
            
        Returns:
            Optional[int]: 変換された出来高（変換できない場合はNone）
        """
        if value is None or value == "":
            return None
        
        try:
            # floatで一度変換してからintに変換（小数点を含む場合があるため）
            float_value = float(value)
            int_value = int(float_value)
            
            # 負の値チェック
            if int_value < 0:
                logger.warning(f"Negative volume value detected: {value}")
                return None
            
            return int_value
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert volume value '{value}': {e}")
            return None
    
    def _convert_bool(self, value: Any) -> bool:
        """
        ブール値への安全な変換
        
        Args:
            value: 変換対象の値
            
        Returns:
            bool: 変換結果
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 't', 'y')
        if isinstance(value, (int, float)):
            return bool(value)
        return False