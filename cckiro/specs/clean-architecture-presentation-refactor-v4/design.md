# Presentation 層クリーンアーキテクチャ改善 第 4 回 設計書

## 1. 設計概要

本設計書では、要件書で定義された 5 つの改善要件を実現するための詳細設計を記述します。
段階的な実装を前提とし、各ステップで動作確認が可能な設計とします。

## 2. アーキテクチャ設計

### 2.1 全体構造

```
app/presentation/
├── middleware/           # ミドルウェア層
│   ├── __init__.py
│   ├── error_handler.py  # エラーハンドリングミドルウェア
│   └── logging.py        # ロギングミドルウェア
├── exceptions/           # Presentation 層固有の例外（新規）
│   ├── __init__.py
│   ├── base.py          # 基底例外クラス
│   └── http_exceptions.py # HTTP 例外クラス
├── schemas/              # 共通スキーマ
│   ├── __init__.py
│   ├── responses.py      # 統一レスポンス構造（新規）
│   └── errors.py         # エラースキーマ（新規）
├── api/
│   └── v1/
│       ├── endpoints/
│       ├── schemas/
│       └── mappers/
├── cli/
│   ├── commands/
│   └── error_handler.py  # CLI 用エラーハンドラー（新規）
└── dependencies/
```

## 3. 詳細設計

### 3.1 統一的なエラーハンドリング機構（REQ-001）

#### 3.1.1 基底例外クラス

```python
# app/presentation/exceptions/base.py

class PresentationError(Exception):
    """Presentation 層の基底例外クラス"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class ValidationError(PresentationError):
    """入力検証エラー"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.field = field

class ResourceNotFoundError(PresentationError):
    """リソース未発見エラー"""
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, error_code="RESOURCE_NOT_FOUND")
```

#### 3.1.2 HTTP エラーマッピング

```python
# app/presentation/exceptions/http_exceptions.py

from fastapi import HTTPException
from app.presentation.exceptions.base import PresentationError

ERROR_STATUS_MAPPING = {
    "VALIDATION_ERROR": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "RESOURCE_NOT_FOUND": 404,
    "CONFLICT": 409,
    "INTERNAL_ERROR": 500,
}

def presentation_error_to_http_exception(error: PresentationError) -> HTTPException:
    """PresentationError を HTTPException に変換"""
    status_code = ERROR_STATUS_MAPPING.get(error.error_code, 500)
    return HTTPException(status_code=status_code, detail=error.message)
```

### 3.2 ミドルウェアレイヤーの実装（REQ-002）

#### 3.2.1 エラーハンドリングミドルウェア

```python
# app/presentation/middleware/error_handler.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.presentation.exceptions.base import PresentationError
from app.presentation.schemas.responses import ErrorResponse

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except PresentationError as e:
            return ErrorResponse(
                success=False,
                error={
                    "code": e.error_code,
                    "message": e.message,
                    "details": getattr(e, "details", None)
                }
            )
        except Exception as e:
            # ログ記録
            return ErrorResponse(
                success=False,
                error={
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred"
                }
            )
```

#### 3.2.2 ロギングミドルウェア

```python
# app/presentation/middleware/logging.py

from fastapi import Request
import time
import logging

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # リクエストログ
        logger.info(f"Request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        # レスポンスログ
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )
        
        return response
```

### 3.3 入力検証の整理（REQ-003）

#### 3.3.1 検証デコレーター

```python
# app/presentation/schemas/validators.py

from functools import wraps
from pydantic import ValidationError as PydanticValidationError
from app.presentation.exceptions.base import ValidationError

def validate_request(schema_class):
    """リクエスト検証デコレーター"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Pydantic の検証を実行
                return await func(*args, **kwargs)
            except PydanticValidationError as e:
                # 統一的なエラー形式に変換
                errors = []
                for error in e.errors():
                    field = ".".join(str(x) for x in error["loc"])
                    message = error["msg"]
                    errors.append({"field": field, "message": message})
                
                raise ValidationError(
                    message="Validation failed",
                    details={"errors": errors}
                )
        return wrapper
    return decorator
```

### 3.4 統一的なレスポンス構造（REQ-004）

#### 3.4.1 基本レスポンス構造

```python
# app/presentation/schemas/responses.py

from typing import Generic, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    """統一レスポンス基底クラス"""
    success: bool
    data: Optional[T] = None
    error: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None

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

class PaginatedResponse(SuccessResponse[List[T]], Generic[T]):
    """ページネーションレスポンス"""
    meta: Dict[str, Any] = {
        "page": 1,
        "per_page": 20,
        "total": 0,
        "total_pages": 0
    }
```

### 3.5 CLI コマンドのエラーハンドリング（REQ-005）

#### 3.5.1 CLI エラーハンドラー

```python
# app/presentation/cli/error_handler.py

import sys
import click
from functools import wraps
from app.presentation.exceptions.base import PresentationError

def handle_cli_errors(func):
    """CLI コマンド用エラーハンドリングデコレーター"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PresentationError as e:
            click.echo(f"Error: {e.message}", err=True)
            if hasattr(e, "details") and e.details:
                click.echo(f"Details: {e.details}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Unexpected error: {str(e)}", err=True)
            sys.exit(2)
    return wrapper
```

## 4. 実装順序

段階的な実装を行うため、以下の順序で実装します：

### Phase 1: 基盤整備
1. 例外クラスの実装（exceptions/）
2. 統一レスポンス構造の実装（schemas/responses.py）

### Phase 2: ミドルウェア実装
3. エラーハンドリングミドルウェアの実装
4. ロギングミドルウェアの実装
5. ミドルウェアの登録

### Phase 3: API 層への適用
6. 既存エンドポイントへの統一レスポンス構造の適用
7. エラーハンドリングの統一

### Phase 4: CLI 層への適用
8. CLI エラーハンドラーの実装
9. 既存 CLI コマンドへの適用

### Phase 5: 検証とテスト
10. 入力検証の整理
11. テストの追加・修正

## 5. 移行戦略

### 5.1 後方互換性の維持
- 既存の API レスポンス形式は、統一レスポンス構造の`data`フィールドに格納
- エラーレスポンスは段階的に移行し、クライアントへの影響を最小化

### 5.2 段階的適用
- 新規エンドポイントから統一構造を適用
- 既存エンドポイントは 1 つずつ慎重に移行

### 5.3 テスト戦略
- 各フェーズごとにユニットテストを追加
- 統合テストで既存機能の動作を保証

## 6. 考慮事項

### 6.1 パフォーマンス
- ミドルウェアのオーバーヘッドを最小化
- ロギングは非同期で実行

### 6.2 拡張性
- 新しいエラータイプの追加が容易な設計
- ミドルウェアの追加・削除が容易な構造

### 6.3 デバッグ容易性
- 詳細なエラー情報の記録
- リクエスト ID によるトレーサビリティ