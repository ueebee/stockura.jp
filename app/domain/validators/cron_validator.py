"""cron 式バリデーターモジュール"""
from datetime import datetime
from typing import Optional

from croniter import croniter

from app.domain.exceptions.schedule_exceptions import InvalidCronExpressionException


def validate_cron_expression(expression: str) -> bool:
    """
    cron 式の妥当性を検証する
    
    Args:
        expression: cron 形式の文字列（例: "0 9 * * *"）
        
    Returns:
        検証成功時は True
        
    Raises:
        InvalidCronExpressionException: 無効な cron 式の場合
    """
    try:
        croniter(expression)
        return True
    except (ValueError, TypeError) as e:
        raise InvalidCronExpressionException(
            f"無効な cron 式です: {expression}. エラー: {str(e)}"
        )


def get_next_run_time(cron_expression: str, base_time: Optional[datetime] = None) -> datetime:
    """
    次回実行時刻を計算する
    
    Args:
        cron_expression: cron 形式の文字列
        base_time: 基準時刻（省略時は現在時刻）
        
    Returns:
        次回実行予定時刻
        
    Raises:
        InvalidCronExpressionException: 無効な cron 式の場合
    """
    try:
        base = base_time or datetime.now()
        cron = croniter(cron_expression, base)
        return cron.get_next(datetime)
    except (ValueError, TypeError) as e:
        raise InvalidCronExpressionException(
            f"無効な cron 式です: {cron_expression}. エラー: {str(e)}"
        )


def get_previous_run_time(cron_expression: str, base_time: Optional[datetime] = None) -> datetime:
    """
    前回実行時刻を計算する
    
    Args:
        cron_expression: cron 形式の文字列
        base_time: 基準時刻（省略時は現在時刻）
        
    Returns:
        前回実行時刻
        
    Raises:
        InvalidCronExpressionException: 無効な cron 式の場合
    """
    try:
        base = base_time or datetime.now()
        cron = croniter(cron_expression, base)
        return cron.get_prev(datetime)
    except (ValueError, TypeError) as e:
        raise InvalidCronExpressionException(
            f"無効な cron 式です: {cron_expression}. エラー: {str(e)}"
        )


def get_cron_description(cron_expression: str) -> str:
    """
    cron 式の説明文を生成する
    
    Args:
        cron_expression: cron 形式の文字列
        
    Returns:
        人間が読みやすい説明文
        
    Raises:
        InvalidCronExpressionException: 無効な cron 式の場合
    """
    validate_cron_expression(cron_expression)
    
    parts = cron_expression.split()
    if len(parts) != 5:
        raise InvalidCronExpressionException(
            f"cron 式は 5 つの要素で構成される必要があります: {cron_expression}"
        )
    
    minute, hour, day, month, weekday = parts
    
    # 一般的なパターンの説明文を生成
    if cron_expression == "0 0 * * *":
        return "毎日 0 時 0 分"
    elif cron_expression == "0 9 * * *":
        return "毎日 9 時 0 分"
    elif cron_expression == "0 9 * * 1-5":
        return "平日（月〜金）9 時 0 分"
    elif cron_expression == "0 9 * * 1":
        return "毎週月曜日 9 時 0 分"
    elif cron_expression == "0 9 1 * *":
        return "毎月 1 日 9 時 0 分"
    elif minute == "0" and hour != "*" and day == "*" and month == "*" and weekday == "*":
        return f"毎日{hour}時 0 分"
    elif minute != "*" and hour != "*" and day == "*" and month == "*" and weekday == "*":
        return f"毎日{hour}時{minute}分"
    else:
        # その他の場合は詳細な説明を生成
        desc_parts = []
        
        if minute != "*":
            desc_parts.append(f"{minute}分")
        if hour != "*":
            desc_parts.append(f"{hour}時")
        if day != "*":
            desc_parts.append(f"{day}日")
        if month != "*":
            desc_parts.append(f"{month}月")
        if weekday != "*":
            weekday_map = {
                "0": "日曜日", "1": "月曜日", "2": "火曜日", "3": "水曜日",
                "4": "木曜日", "5": "金曜日", "6": "土曜日"
            }
            if weekday in weekday_map:
                desc_parts.append(weekday_map[weekday])
            else:
                desc_parts.append(f"曜日指定 ({weekday})")
        
        return "、".join(desc_parts) + "に実行"