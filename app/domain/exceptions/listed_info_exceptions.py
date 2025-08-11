"""Listed info related exceptions."""

from app.domain.exceptions.base import DomainException


class ListedInfoError(DomainException):
    """上場銘柄情報関連の基底例外"""

    pass


class ListedInfoAPIError(ListedInfoError):
    """API 通信エラー"""

    pass


class ListedInfoDataError(ListedInfoError):
    """データ形式エラー"""

    pass


class ListedInfoStorageError(ListedInfoError):
    """データ保存エラー"""

    pass


class ListedInfoNotFoundError(ListedInfoError):
    """上場銘柄情報が見つからないエラー"""

    pass