"""
CLI エラーハンドラーのユニットテスト
"""

import sys
import pytest
from unittest.mock import Mock, patch
import click

from app.presentation.cli.error_handler import handle_cli_errors, handle_async_cli_errors
from app.presentation.exceptions import PresentationError, ValidationError, UnauthorizedError
from app.domain.exceptions.base import DomainException


class TestHandleCliErrors:
    """同期 CLI エラーハンドラーのテスト"""
    
    def test_successful_execution(self):
        """正常実行時のテスト"""
        @handle_cli_errors
        def test_command():
            return "Success"
        
        result = test_command()
        assert result == "Success"
    
    def test_presentation_error_handling(self):
        """PresentationError のハンドリングテスト"""
        @handle_cli_errors
        def test_command():
            raise ValidationError("Invalid input", details={"field": "email"})
        
        with patch("click.echo") as mock_echo, pytest.raises(SystemExit) as exc_info:
            test_command()
        
        # エラーメッセージが出力されることを確認
        mock_echo.assert_called()
        assert exc_info.value.code == 1
    
    def test_domain_exception_handling(self):
        """DomainException のハンドリングテスト"""
        @handle_cli_errors
        def test_command():
            raise DomainException("Business rule violation")
        
        with patch("click.echo") as mock_echo, pytest.raises(SystemExit) as exc_info:
            test_command()
        
        mock_echo.assert_called()
        assert exc_info.value.code == 1
    
    def test_click_exception_propagation(self):
        """ClickException がそのまま伝播することのテスト"""
        @handle_cli_errors
        def test_command():
            raise click.ClickException("Click error")
        
        with pytest.raises(click.ClickException) as exc_info:
            test_command()
        
        assert str(exc_info.value) == "Click error"
    
    def test_keyboard_interrupt_handling(self):
        """KeyboardInterrupt のハンドリングテスト"""
        @handle_cli_errors
        def test_command():
            raise KeyboardInterrupt()
        
        with patch("click.echo") as mock_echo, pytest.raises(SystemExit) as exc_info:
            test_command()
        
        mock_echo.assert_called_with("\nOperation cancelled by user.", err=True)
        assert exc_info.value.code == 130
    
    def test_unexpected_error_handling(self):
        """予期しないエラーのハンドリングテスト"""
        @handle_cli_errors
        def test_command():
            raise RuntimeError("Unexpected error")
        
        with patch("click.echo") as mock_echo, pytest.raises(SystemExit) as exc_info:
            test_command()
        
        # 複数回 echo が呼ばれることを確認
        assert mock_echo.call_count >= 2
        assert exc_info.value.code == 2


class TestHandleAsyncCliErrors:
    """非同期 CLI エラーハンドラーのテスト"""
    
    def test_async_successful_execution(self):
        """非同期正常実行時のテスト"""
        @handle_async_cli_errors
        async def test_command():
            return "Async Success"
        
        # handle_async_cli_errors は同期ラッパーを返すので、直接呼び出せる
        result = test_command()
        assert result == "Async Success"
    
    def test_async_validation_error_handling(self):
        """非同期での ValidationError ハンドリングテスト"""
        @handle_async_cli_errors
        async def test_command():
            raise ValidationError("Async validation error", 
                               error_code="ASYNC_VALIDATION",
                               details={"async": True})
        
        with patch("click.echo") as mock_echo, pytest.raises(SystemExit) as exc_info:
            test_command()
        
        mock_echo.assert_called()
        assert exc_info.value.code == 1
    
    def test_async_unauthorized_error_with_details(self):
        """詳細情報付き UnauthorizedError のハンドリングテスト"""
        @handle_async_cli_errors
        async def test_command():
            raise UnauthorizedError("Authentication failed", 
                                  details={"reason": "Token expired"})
        
        with patch("click.echo") as mock_echo, pytest.raises(SystemExit) as exc_info:
            test_command()
        
        # エラーメッセージと詳細の両方が出力されることを確認
        calls = mock_echo.call_args_list
        assert len(calls) >= 2  # エラーメッセージと詳細情報
        assert exc_info.value.code == 1