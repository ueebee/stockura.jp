# Presentation 層の共通スキーマ

from app.presentation.schemas.responses import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginationMeta,
)
from app.presentation.schemas.errors import (
    ValidationErrorDetail,
    ValidationErrorResponse,
    ErrorDetail,
    ErrorMessageFormat,
)

__all__ = [
    # Response schemas
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationMeta",
    # Error schemas
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    "ErrorDetail",
    "ErrorMessageFormat",
]