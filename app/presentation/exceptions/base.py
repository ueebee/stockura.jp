"""
Presentation 層の基底例外クラス
"""

from typing import Optional, Any, Dict


class PresentationError(Exception):
    """Presentation 層の基底例外クラス"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "PRESENTATION_ERROR"
        self.details = details or {}


class ValidationError(PresentationError):
    """入力検証エラー"""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)
        self.field = field
        if field:
            self.details["field"] = field


class ResourceNotFoundError(PresentationError):
    """リソース未発見エラー"""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, error_code="RESOURCE_NOT_FOUND")
        self.resource = resource
        self.identifier = identifier
        self.details = {
            "resource": resource,
            "identifier": identifier
        }


class UnauthorizedError(PresentationError):
    """認証エラー"""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, error_code="UNAUTHORIZED")


class ForbiddenError(PresentationError):
    """認可エラー"""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, error_code="FORBIDDEN")


class ConflictError(PresentationError):
    """競合エラー"""
    
    def __init__(
        self, 
        message: str, 
        resource: Optional[str] = None,
        identifier: Optional[str] = None
    ):
        super().__init__(message, error_code="CONFLICT")
        if resource:
            self.details["resource"] = resource
        if identifier:
            self.details["identifier"] = identifier