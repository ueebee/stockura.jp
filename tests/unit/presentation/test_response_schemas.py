"""
統一レスポンススキーマのユニットテスト
"""

import pytest
from pydantic import ValidationError as PydanticValidationError
from app.presentation.schemas.responses import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
)


class TestBaseResponse:
    """BaseResponse のテスト"""
    
    def test_base_response_success(self):
        """成功レスポンスの基本テスト"""
        response = BaseResponse(
            success=True,
            data={"message": "Hello"},
            error=None,
            meta={"version": "1.0"}
        )
        assert response.success is True
        assert response.data == {"message": "Hello"}
        assert response.error is None
        assert response.meta == {"version": "1.0"}
    
    def test_base_response_error(self):
        """エラーレスポンスの基本テスト"""
        response = BaseResponse(
            success=False,
            data=None,
            error={"code": "ERROR_CODE", "message": "Error occurred"},
            meta=None
        )
        assert response.success is False
        assert response.data is None
        assert response.error == {"code": "ERROR_CODE", "message": "Error occurred"}
        assert response.meta is None


class TestSuccessResponse:
    """SuccessResponse のテスト"""
    
    def test_success_response_simple_data(self):
        """シンプルなデータの成功レスポンス"""
        response = SuccessResponse(data="Hello World")
        assert response.success is True
        assert response.data == "Hello World"
        assert response.error is None
    
    def test_success_response_complex_data(self):
        """複雑なデータの成功レスポンス"""
        data = {
            "user": {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com"
            },
            "permissions": ["read", "write"]
        }
        response = SuccessResponse(data=data)
        assert response.success is True
        assert response.data == data
        assert response.error is None
    
    def test_success_response_with_meta(self):
        """メタデータ付き成功レスポンス"""
        response = SuccessResponse(
            data={"id": 1},
            meta={"timestamp": "2025-08-11T10:00:00Z"}
        )
        assert response.success is True
        assert response.data == {"id": 1}
        assert response.meta == {"timestamp": "2025-08-11T10:00:00Z"}


class TestErrorResponse:
    """ErrorResponse のテスト"""
    
    def test_error_response_basic(self):
        """基本的なエラーレスポンス"""
        response = ErrorResponse(
            error={
                "code": "VALIDATION_ERROR",
                "message": "Validation failed"
            }
        )
        assert response.success is False
        assert response.data is None
        assert response.error["code"] == "VALIDATION_ERROR"
        assert response.error["message"] == "Validation failed"
    
    def test_error_response_with_details(self):
        """詳細情報付きエラーレスポンス"""
        error_details = {
            "code": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": {
                "field": "email",
                "reason": "Invalid format"
            }
        }
        response = ErrorResponse(error=error_details)
        assert response.success is False
        assert response.error == error_details
    
    def test_error_response_with_meta(self):
        """メタデータ付きエラーレスポンス"""
        response = ErrorResponse(
            error={"code": "ERROR", "message": "An error occurred"},
            meta={"request_id": "123456"}
        )
        assert response.success is False
        assert response.meta == {"request_id": "123456"}


class TestPaginatedResponse:
    """PaginatedResponse のテスト"""
    
    def test_paginated_response_basic(self):
        """基本的なページネーションレスポンス"""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginatedResponse(
            data=items,
            total=10,
            page=1,
            per_page=3
        )
        assert response.success is True
        assert response.data == items
        assert response.total == 10
        assert response.page == 1
        assert response.per_page == 3
        assert response.pages == 4  # ceil(10/3) = 4
    
    def test_paginated_response_single_page(self):
        """単一ページのページネーションレスポンス"""
        items = [{"id": 1}, {"id": 2}]
        response = PaginatedResponse(
            data=items,
            total=2,
            page=1,
            per_page=10
        )
        assert response.pages == 1
    
    def test_paginated_response_empty(self):
        """空のページネーションレスポンス"""
        response = PaginatedResponse(
            data=[],
            total=0,
            page=1,
            per_page=10
        )
        assert response.data == []
        assert response.total == 0
        assert response.pages == 0
    
    def test_paginated_response_with_meta(self):
        """メタデータ付きページネーションレスポンス"""
        response = PaginatedResponse(
            data=[{"id": 1}],
            total=1,
            page=1,
            per_page=10,
            meta={"filter": "active"}
        )
        assert response.meta == {"filter": "active"}
    
    def test_paginated_response_validation_error(self):
        """不正なページ番号でのバリデーションエラー"""
        with pytest.raises(PydanticValidationError):
            PaginatedResponse(
                data=[],
                total=10,
                page=0,  # ページ番号は 1 以上である必要がある
                per_page=10
            )
    
    def test_paginated_response_validation_error_per_page(self):
        """不正な per_page でのバリデーションエラー"""
        with pytest.raises(PydanticValidationError):
            PaginatedResponse(
                data=[],
                total=10,
                page=1,
                per_page=0  # per_page は 1 以上である必要がある
            )