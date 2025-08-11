"""
検証デコレーター

Pydantic モデルを使用した入力検証を提供します。
"""

from functools import wraps
from typing import Callable, Type, TypeVar, Any
from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.presentation.exceptions import ValidationError


T = TypeVar("T", bound=BaseModel)


def validate_request(model: Type[T]) -> Callable:
    """
    リクエストボディを Pydantic モデルで検証するデコレーター
    
    Args:
        model: 検証に使用する Pydantic モデルクラス
        
    Returns:
        デコレートされた関数
        
    Raises:
        ValidationError: 検証エラーが発生した場合
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # リクエストボディを探す
            request_data = None
            for arg in args:
                if isinstance(arg, dict):
                    request_data = arg
                    break
            
            for key, value in kwargs.items():
                if key in ["request", "data", "body"]:
                    request_data = value
                    break
            
            if request_data is None:
                raise ValidationError("リクエストボディが見つかりません")
            
            try:
                # Pydantic モデルで検証
                validated_data = model(**request_data)
                # 検証済みデータを kwargs に追加
                kwargs["validated_data"] = validated_data
                return await func(*args, **kwargs)
            except PydanticValidationError as e:
                errors = []
                for error in e.errors():
                    field = ".".join(str(x) for x in error["loc"])
                    errors.append(f"{field}: {error['msg']}")
                
                raise ValidationError(
                    "入力検証エラー",
                    error_code="VALIDATION_ERROR",
                    details={"errors": errors}
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # リクエストボディを探す
            request_data = None
            for arg in args:
                if isinstance(arg, dict):
                    request_data = arg
                    break
            
            for key, value in kwargs.items():
                if key in ["request", "data", "body"]:
                    request_data = value
                    break
            
            if request_data is None:
                raise ValidationError("リクエストボディが見つかりません")
            
            try:
                # Pydantic モデルで検証
                validated_data = model(**request_data)
                # 検証済みデータを kwargs に追加
                kwargs["validated_data"] = validated_data
                return func(*args, **kwargs)
            except PydanticValidationError as e:
                errors = []
                for error in e.errors():
                    field = ".".join(str(x) for x in error["loc"])
                    errors.append(f"{field}: {error['msg']}")
                
                raise ValidationError(
                    "入力検証エラー",
                    error_code="VALIDATION_ERROR",
                    details={"errors": errors}
                )
        
        # 関数が非同期かどうかを判定
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_query_params(**validators) -> Callable:
    """
    クエリパラメータを検証するデコレーター
    
    Args:
        **validators: パラメータ名と検証関数のマッピング
        
    Returns:
        デコレートされた関数
        
    Raises:
        ValidationError: 検証エラーが発生した場合
        
    Example:
        @validate_query_params(
            page=lambda x: x > 0,
            per_page=lambda x: 1 <= x <= 100
        )
        async def list_items(page: int = 1, per_page: int = 20):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            errors = []
            
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    try:
                        if not validator(value):
                            errors.append(f"{param_name}: 無効な値です")
                    except Exception as e:
                        errors.append(f"{param_name}: {str(e)}")
            
            if errors:
                raise ValidationError(
                    "クエリパラメータ検証エラー",
                    error_code="QUERY_VALIDATION_ERROR",
                    details={"errors": errors}
                )
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            errors = []
            
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    try:
                        if not validator(value):
                            errors.append(f"{param_name}: 無効な値です")
                    except Exception as e:
                        errors.append(f"{param_name}: {str(e)}")
            
            if errors:
                raise ValidationError(
                    "クエリパラメータ検証エラー",
                    error_code="QUERY_VALIDATION_ERROR",
                    details={"errors": errors}
                )
            
            return func(*args, **kwargs)
        
        # 関数が非同期かどうかを判定
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_path_params(**validators) -> Callable:
    """
    パスパラメータを検証するデコレーター
    
    Args:
        **validators: パラメータ名と検証関数のマッピング
        
    Returns:
        デコレートされた関数
        
    Raises:
        ValidationError: 検証エラーが発生した場合
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            errors = []
            
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    try:
                        if not validator(value):
                            errors.append(f"{param_name}: 無効な値です")
                    except Exception as e:
                        errors.append(f"{param_name}: {str(e)}")
            
            if errors:
                raise ValidationError(
                    "パスパラメータ検証エラー",
                    error_code="PATH_VALIDATION_ERROR",
                    details={"errors": errors}
                )
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            errors = []
            
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    try:
                        if not validator(value):
                            errors.append(f"{param_name}: 無効な値です")
                    except Exception as e:
                        errors.append(f"{param_name}: {str(e)}")
            
            if errors:
                raise ValidationError(
                    "パスパラメータ検証エラー",
                    error_code="PATH_VALIDATION_ERROR",
                    details={"errors": errors}
                )
            
            return func(*args, **kwargs)
        
        # 関数が非同期かどうかを判定
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator