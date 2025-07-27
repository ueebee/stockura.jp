"""J-Quants API 関連の例外定義"""


class JQuantsException(Exception):
    """J-Quants API 関連の基底例外クラス"""

    pass


class AuthenticationError(JQuantsException):
    """認証エラー"""

    pass


class TokenRefreshError(JQuantsException):
    """トークンリフレッシュエラー"""

    pass


class NetworkError(JQuantsException):
    """ネットワークエラー"""

    pass


class RateLimitError(JQuantsException):
    """レート制限エラー"""

    pass


class StorageError(JQuantsException):
    """ストレージエラー"""

    pass


class ValidationError(JQuantsException):
    """バリデーションエラー"""

    pass


class DataNotFoundError(JQuantsException):
    """データが見つからないエラー"""

    pass
