"""
Presentation 層の例外クラス

このモジュールは、 Presentation 層で使用される例外クラスを定義します。
"""

from app.presentation.exceptions.base import (
    PresentationError,
    ValidationError,
    ResourceNotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
)
from app.presentation.exceptions.http_exceptions import (
    presentation_error_to_http_exception,
    ERROR_STATUS_MAPPING,
)

__all__ = [
    "PresentationError",
    "ValidationError",
    "ResourceNotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "ConflictError",
    "presentation_error_to_http_exception",
    "ERROR_STATUS_MAPPING",
]