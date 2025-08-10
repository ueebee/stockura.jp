"""スケジュールプリセット定義モジュール"""
from typing import Dict, Optional


# プリセット定義（キー: プリセット名、値: (cron 式, 説明)）
SCHEDULE_PRESETS: Dict[str, tuple[str, str]] = {
    # 毎日実行パターン
    "daily_morning": ("0 9 * * *", "毎日朝 9 時に実行"),
    "daily_noon": ("0 12 * * *", "毎日正午に実行"),
    "daily_evening": ("0 18 * * *", "毎日夕方 6 時に実行"),
    "daily_night": ("0 21 * * *", "毎日夜 9 時に実行"),
    "daily_midnight": ("0 0 * * *", "毎日深夜 0 時に実行"),
    
    # 営業日（平日）実行パターン
    "business_days_morning": ("0 9 * * 1-5", "平日朝 9 時に実行"),
    "business_days_evening": ("0 18 * * 1-5", "平日夕方 6 時に実行"),
    
    # 週次実行パターン
    "weekly_monday": ("0 9 * * 1", "毎週月曜日朝 9 時に実行"),
    "weekly_friday": ("0 18 * * 5", "毎週金曜日夕方 6 時に実行"),
    "weekly_sunday": ("0 9 * * 0", "毎週日曜日朝 9 時に実行"),
    
    # 月次実行パターン
    "monthly_first": ("0 9 1 * *", "毎月 1 日朝 9 時に実行"),
    "monthly_last_business_day": ("0 18 28-31 * *", "毎月末付近の夕方 6 時に実行"),
    
    # マーケット時間に合わせたパターン
    "market_open": ("0 9 * * 1-5", "市場開場時（平日 9 時）に実行"),
    "market_close": ("0 15 * * 1-5", "市場閉場時（平日 15 時）に実行"),
    "after_market": ("0 16 * * 1-5", "市場閉場後（平日 16 時）に実行"),
    
    # 頻度の高い実行パターン
    "every_hour": ("0 * * * *", "毎時 0 分に実行"),
    "every_30_minutes": ("0,30 * * * *", "30 分ごとに実行"),
    "every_15_minutes": ("0,15,30,45 * * * *", "15 分ごとに実行"),
}


def get_preset_cron_expression(preset_name: str) -> Optional[str]:
    """
    プリセット名から cron 式を取得する
    
    Args:
        preset_name: プリセット名
        
    Returns:
        cron 式（プリセットが存在しない場合は None）
    """
    preset = SCHEDULE_PRESETS.get(preset_name)
    return preset[0] if preset else None


def get_preset_description(preset_name: str) -> Optional[str]:
    """
    プリセット名から説明文を取得する
    
    Args:
        preset_name: プリセット名
        
    Returns:
        説明文（プリセットが存在しない場合は None）
    """
    preset = SCHEDULE_PRESETS.get(preset_name)
    return preset[1] if preset else None


def list_presets() -> Dict[str, Dict[str, str]]:
    """
    利用可能なプリセット一覧を取得する
    
    Returns:
        プリセット情報の辞書
    """
    return {
        name: {
            "cron_expression": cron_expr,
            "description": description
        }
        for name, (cron_expr, description) in SCHEDULE_PRESETS.items()
    }


def get_preset_by_cron(cron_expression: str) -> Optional[str]:
    """
    cron 式からプリセット名を逆引きする
    
    Args:
        cron_expression: cron 式
        
    Returns:
        プリセット名（該当するプリセットがない場合は None）
    """
    for name, (cron_expr, _) in SCHEDULE_PRESETS.items():
        if cron_expr == cron_expression:
            return name
    return None


def get_presets_by_category(category: str) -> Dict[str, Dict[str, str]]:
    """
    カテゴリ別にプリセットを取得する
    
    Args:
        category: カテゴリ名（"daily", "weekly", "monthly", "market", "frequent"）
        
    Returns:
        該当するプリセット情報の辞書
    """
    category_filters = {
        "daily": lambda name: name.startswith("daily_") or name.startswith("business_days_"),
        "weekly": lambda name: name.startswith("weekly_"),
        "monthly": lambda name: name.startswith("monthly_"),
        "market": lambda name: "market" in name or name.startswith("after_market"),
        "frequent": lambda name: "every_" in name,
    }
    
    filter_func = category_filters.get(category.lower())
    if not filter_func:
        return {}
    
    return {
        name: {
            "cron_expression": cron_expr,
            "description": description
        }
        for name, (cron_expr, description) in SCHEDULE_PRESETS.items()
        if filter_func(name)
    }