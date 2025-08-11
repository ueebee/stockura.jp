"""
CLI 用エラーハンドリング機能
"""

import sys
import click
import logging
from functools import wraps
from typing import Callable, Any

from app.presentation.exceptions.base import PresentationError
from app.domain.exceptions.base import DomainException


logger = logging.getLogger(__name__)


def handle_cli_errors(func: Callable) -> Callable:
    """
    CLI コマンド用エラーハンドリングデコレーター
    
    統一的なエラーハンドリングを提供し、適切な終了コードを設定します。
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
            
        except PresentationError as e:
            # Presentation 層のエラー
            click.echo(click.style(f"Error: {e.message}", fg="red"), err=True)
            if hasattr(e, "details") and e.details:
                click.echo(f"Details: {e.details}", err=True)
            sys.exit(1)
            
        except DomainException as e:
            # ドメイン層のエラー
            click.echo(click.style(f"Business Error: {str(e)}", fg="red"), err=True)
            sys.exit(1)
            
        except click.ClickException:
            # Click 自体のエラーはそのまま再発生
            raise
            
        except KeyboardInterrupt:
            # Ctrl+C による中断
            click.echo("\nOperation cancelled by user.", err=True)
            sys.exit(130)  # 130 = 128 + SIGINT
            
        except Exception as e:
            # 予期しないエラー
            logger.exception("Unexpected error occurred in CLI command")
            click.echo(
                click.style(f"Unexpected error: {str(e)}", fg="red", bold=True), 
                err=True
            )
            click.echo("Please check the logs for more details.", err=True)
            sys.exit(2)
            
    return wrapper


def handle_async_cli_errors(func: Callable) -> Callable:
    """
    非同期 CLI コマンド用エラーハンドリングデコレーター
    
    asyncio を使用するコマンド用のエラーハンドリングを提供します。
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
            
        except PresentationError as e:
            # Presentation 層のエラー
            click.echo(click.style(f"Error: {e.message}", fg="red"), err=True)
            if hasattr(e, "details") and e.details:
                click.echo(f"Details: {e.details}", err=True)
            sys.exit(1)
            
        except DomainException as e:
            # ドメイン層のエラー
            click.echo(click.style(f"Business Error: {str(e)}", fg="red"), err=True)
            sys.exit(1)
            
        except click.ClickException:
            # Click 自体のエラーはそのまま再発生
            raise
            
        except KeyboardInterrupt:
            # Ctrl+C による中断
            click.echo("\nOperation cancelled by user.", err=True)
            sys.exit(130)
            
        except Exception as e:
            # 予期しないエラー
            logger.exception("Unexpected error occurred in async CLI command")
            click.echo(
                click.style(f"Unexpected error: {str(e)}", fg="red", bold=True), 
                err=True
            )
            click.echo("Please check the logs for more details.", err=True)
            sys.exit(2)
            
    # 同期関数でラップして返す
    @wraps(func)
    def wrapper(*args, **kwargs):
        import asyncio
        return asyncio.run(async_wrapper(*args, **kwargs))
        
    return wrapper