"""スケジュール関連の例外定義"""

from app.domain.exceptions.base import DomainException


class ScheduleException(DomainException):
    """スケジュール関連の基底例外クラス"""
    pass


class InvalidCronExpressionException(ScheduleException):
    """無効な cron 式に関する例外"""
    pass


class ScheduleConflictException(ScheduleException):
    """スケジュール名の重複など、競合に関する例外"""
    pass


class ScheduleNotFoundException(ScheduleException):
    """スケジュールが見つからない場合の例外"""
    pass


class ScheduleValidationException(ScheduleException):
    """スケジュールのバリデーションエラーに関する例外"""
    pass


class ScheduleExecutionException(ScheduleException):
    """スケジュール実行時のエラーに関する例外"""
    pass