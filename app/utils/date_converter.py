"""
日付変換ユーティリティ

様々な形式の日付データを統一的に扱うためのユーティリティクラス
"""

from typing import Optional, Union
from datetime import datetime, date


class DateConverter:
    """日付変換ユーティリティクラス"""
    
    @staticmethod
    def to_date(date_input: Optional[Union[str, datetime, date]]) -> Optional[date]:
        """
        様々な形式の日付入力をdateオブジェクトに変換
        
        Args:
            date_input: 日付入力（str, datetime, date, None）
            
        Returns:
            Optional[date]: 変換されたdateオブジェクト
            
        Raises:
            ValueError: サポートされていない形式の場合
        """
        if date_input is None:
            return None
        
        if isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, date):
            return date_input
        elif isinstance(date_input, str):
            # YYYYMMDD形式の場合
            if len(date_input) == 8 and date_input.isdigit():
                try:
                    return date(
                        int(date_input[:4]),
                        int(date_input[4:6]),
                        int(date_input[6:8])
                    )
                except ValueError:
                    raise ValueError(f"Invalid date value in YYYYMMDD format: {date_input}")
            # YYYY-MM-DD形式の場合
            else:
                try:
                    return date.fromisoformat(date_input)
                except ValueError:
                    raise ValueError(f"Unsupported date string format: {date_input}")
        
        raise ValueError(f"Unsupported date type: {type(date_input)}")
    
    @staticmethod
    def to_yyyymmdd_string(date_obj: Optional[date]) -> Optional[str]:
        """
        dateオブジェクトをYYYYMMDD形式の文字列に変換
        
        Args:
            date_obj: dateオブジェクト
            
        Returns:
            Optional[str]: YYYYMMDD形式の文字列
        """
        if date_obj is None:
            return None
        
        return date_obj.strftime("%Y%m%d")
    
    @staticmethod
    def to_iso_string(date_obj: Optional[date]) -> Optional[str]:
        """
        dateオブジェクトをYYYY-MM-DD形式の文字列に変換
        
        Args:
            date_obj: dateオブジェクト
            
        Returns:
            Optional[str]: YYYY-MM-DD形式の文字列
        """
        if date_obj is None:
            return None
        
        return date_obj.isoformat()