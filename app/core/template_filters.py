"""
Jinja2 カスタムテンプレートフィルタ
"""
from datetime import datetime
from typing import Optional
import pytz


def to_jst(dt: Optional[datetime]) -> Optional[str]:
    """
    UTC datetimeをJSTに変換して文字列として返す
    
    Args:
        dt: UTC datetime オブジェクト
        
    Returns:
        JSTに変換された時刻文字列 (YYYY-MM-DD HH:MM)
    """
    if not dt:
        return None
    
    # datetimeがnaiveな場合はUTCとして扱う
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # JSTに変換
    jst = pytz.timezone('Asia/Tokyo')
    dt_jst = dt.astimezone(jst)
    
    return dt_jst.strftime('%Y-%m-%d %H:%M')


def to_jst_with_seconds(dt: Optional[datetime]) -> Optional[str]:
    """
    UTC datetimeをJSTに変換して秒まで含む文字列として返す
    
    Args:
        dt: UTC datetime オブジェクト
        
    Returns:
        JSTに変換された時刻文字列 (YYYY-MM-DD HH:MM:SS)
    """
    if not dt:
        return None
    
    # datetimeがnaiveな場合はUTCとして扱う
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # JSTに変換
    jst = pytz.timezone('Asia/Tokyo')
    dt_jst = dt.astimezone(jst)
    
    return dt_jst.strftime('%Y-%m-%d %H:%M:%S')