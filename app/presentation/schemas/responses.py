"""
統一レスポンス構造の定義
"""

from typing import Generic, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel, Field


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """
    統一レスポンス基底クラス
    
    すべての API レスポンスはこの構造に従います。
    """
    success: bool = Field(..., description="リクエストの成功/失敗を示すフラグ")
    data: Optional[T] = Field(None, description="レスポンスデータ")
    error: Optional[Dict[str, Any]] = Field(None, description="エラー情報")
    meta: Optional[Dict[str, Any]] = Field(None, description="メタデータ（ページネーション情報など）")


class SuccessResponse(BaseResponse[T], Generic[T]):
    """成功レスポンス"""
    success: bool = True
    data: T
    error: None = None


class ErrorResponse(BaseResponse[None]):
    """エラーレスポンス"""
    success: bool = False
    data: None = None
    error: Dict[str, Any]
    
    @classmethod
    def from_error(cls, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        """エラー情報からレスポンスを生成"""
        error_info = {
            "code": error_code,
            "message": message,
        }
        if details:
            error_info["details"] = details
            
        return cls(error=error_info)


class PaginationMeta(BaseModel):
    """ページネーション用メタデータ"""
    page: int = Field(1, ge=1, description="現在のページ番号")
    per_page: int = Field(20, ge=1, le=100, description="1 ページあたりの件数")
    total: int = Field(0, ge=0, description="総件数")
    total_pages: int = Field(0, ge=0, description="総ページ数")


class PaginatedResponse(SuccessResponse[List[T]], Generic[T]):
    """ページネーションレスポンス"""
    meta: Dict[str, Any]
    
    @classmethod
    def from_data(
        cls, 
        data: List[T], 
        page: int = 1, 
        per_page: int = 20,
        total: int = 0
    ):
        """データとページネーション情報からレスポンスを生成"""
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        meta = PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages
        )
        
        return cls(
            data=data,
            meta=meta.model_dump()
        )