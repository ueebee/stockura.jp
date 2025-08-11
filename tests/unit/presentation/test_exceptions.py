"""
Presentation 層の例外クラスのユニットテスト
"""

import pytest
from app.presentation.exceptions import (
    PresentationError,
    ValidationError,
    ResourceNotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
)
from app.presentation.exceptions.http_exceptions import get_status_code_for_exception


class TestPresentationExceptions:
    """Presentation 層例外のテスト"""
    
    def test_presentation_error_basic(self):
        """基本的な PresentationError のテスト"""
        error = PresentationError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code == "PRESENTATION_ERROR"
        assert error.details == {}
    
    def test_presentation_error_with_details(self):
        """詳細情報付き PresentationError のテスト"""
        details = {"field": "value", "count": 42}
        error = PresentationError("Test error", error_code="CUSTOM_ERROR", details=details)
        assert error.message == "Test error"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.details == details
    
    def test_validation_error(self):
        """ValidationError のテスト"""
        error = ValidationError("Invalid input", details={"field": "email", "reason": "invalid format"})
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field"] == "email"
        assert error.details["reason"] == "invalid format"
    
    def test_resource_not_found_error(self):
        """ResourceNotFoundError のテスト"""
        error = ResourceNotFoundError("User not found", details={"user_id": "123"})
        assert error.message == "User not found"
        assert error.error_code == "RESOURCE_NOT_FOUND"
        assert error.details["user_id"] == "123"
    
    def test_unauthorized_error(self):
        """UnauthorizedError のテスト"""
        error = UnauthorizedError("Invalid credentials")
        assert error.message == "Invalid credentials"
        assert error.error_code == "UNAUTHORIZED"
    
    def test_forbidden_error(self):
        """ForbiddenError のテスト"""
        error = ForbiddenError("Access denied")
        assert error.message == "Access denied"
        assert error.error_code == "FORBIDDEN"
    
    def test_conflict_error(self):
        """ConflictError のテスト"""
        error = ConflictError("Resource already exists", details={"name": "test-resource"})
        assert error.message == "Resource already exists"
        assert error.error_code == "CONFLICT"
        assert error.details["name"] == "test-resource"


class TestHTTPMapping:
    """HTTP 例外マッピングのテスト"""
    
    def test_get_status_code_for_validation_error(self):
        """ValidationError のステータスコードマッピング"""
        error = ValidationError("Invalid input")
        status_code = get_status_code_for_exception(error)
        assert status_code == 400
    
    def test_get_status_code_for_unauthorized_error(self):
        """UnauthorizedError のステータスコードマッピング"""
        error = UnauthorizedError("Not authenticated")
        status_code = get_status_code_for_exception(error)
        assert status_code == 401
    
    def test_get_status_code_for_forbidden_error(self):
        """ForbiddenError のステータスコードマッピング"""
        error = ForbiddenError("Access denied")
        status_code = get_status_code_for_exception(error)
        assert status_code == 403
    
    def test_get_status_code_for_resource_not_found_error(self):
        """ResourceNotFoundError のステータスコードマッピング"""
        error = ResourceNotFoundError("Not found")
        status_code = get_status_code_for_exception(error)
        assert status_code == 404
    
    def test_get_status_code_for_conflict_error(self):
        """ConflictError のステータスコードマッピング"""
        error = ConflictError("Already exists")
        status_code = get_status_code_for_exception(error)
        assert status_code == 409
    
    def test_get_status_code_for_generic_presentation_error(self):
        """一般的な PresentationError のステータスコードマッピング"""
        error = PresentationError("Generic error")
        status_code = get_status_code_for_exception(error)
        assert status_code == 500
    
    def test_get_status_code_for_unknown_exception(self):
        """未知の例外のステータスコードマッピング"""
        error = Exception("Unknown error")
        status_code = get_status_code_for_exception(error)
        assert status_code == 500