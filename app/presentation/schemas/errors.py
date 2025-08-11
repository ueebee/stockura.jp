"""
エラー関連のスキーマ定義
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ValidationErrorDetail(BaseModel):
    """検証エラーの詳細情報"""
    field: str = Field(..., description="エラーが発生したフィールド名")
    message: str = Field(..., description="エラーメッセージ")
    type: Optional[str] = Field(None, description="エラータイプ")


class ValidationErrorResponse(BaseModel):
    """検証エラーレスポンス"""
    errors: List[ValidationErrorDetail] = Field(..., description="検証エラーのリスト")


class ErrorDetail(BaseModel):
    """一般的なエラー詳細"""
    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")
    details: Optional[Dict[str, Any]] = Field(None, description="追加のエラー詳細情報")


class ErrorMessageFormat(BaseModel):
    """エラーメッセージのフォーマット"""
    error_code: str = Field(..., description="エラーコード")
    user_message: str = Field(..., description="ユーザー向けメッセージ")
    developer_message: Optional[str] = Field(None, description="開発者向けメッセージ")
    trace_id: Optional[str] = Field(None, description="トレース ID")