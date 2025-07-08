"""
外部API関連のテストフィクスチャ

外部APIのモック、レスポンスデータ、HTTPクライアントの設定を提供します。
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, date
import json
from typing import Dict, Any, Optional

import httpx


@pytest.fixture
def mock_jquants_client():
    """
    J-Quants APIクライアントのモックを提供するフィクスチャ
    
    使用例:
        mock_jquants_client.get_listed_info.return_value = {...}
    """
    mock = Mock()
    
    # 各メソッドをAsyncMockとして設定
    mock.get_listed_info = AsyncMock()
    mock.get_daily_quotes = AsyncMock()
    mock.refresh_tokens = AsyncMock()
    mock._ensure_valid_token = AsyncMock()
    mock.close = AsyncMock()
    
    # デフォルトの戻り値を設定
    mock.get_listed_info.return_value = {
        "info": [
            {
                "Date": "2024-01-01",
                "Code": "72030",
                "CompanyName": "トヨタ自動車",
                "MarketCode": "0111"
            }
        ]
    }
    
    mock.get_daily_quotes.return_value = {
        "daily_quotes": [
            {
                "Date": "2024-01-01",
                "Code": "72030",
                "Open": 2500.0,
                "High": 2550.0,
                "Low": 2480.0,
                "Close": 2520.0,
                "Volume": 15000000
            }
        ]
    }
    
    return mock


@pytest.fixture
def mock_httpx_client():
    """
    HTTPXクライアントのモックを提供するフィクスチャ
    
    外部API呼び出しをモック化します。
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.raise_for_status = Mock()
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.delete.return_value = mock_response
    
    return mock_client


@pytest.fixture
def jquants_response_builder():
    """
    J-Quants APIレスポンスを構築するヘルパーを提供
    
    テストシナリオに応じたレスポンスデータを簡単に作成できます。
    """
    class ResponseBuilder:
        @staticmethod
        def build_listed_info(companies: list) -> dict:
            """上場企業情報レスポンスを構築"""
            return {
                "info": [
                    {
                        "Date": company.get("date", "2024-01-01"),
                        "Code": company["code"],
                        "CompanyName": company["name"],
                        "CompanyNameEnglish": company.get("name_english", company["name"]),
                        "Sector17Code": company.get("sector17", "1"),
                        "Sector17CodeName": company.get("sector17_name", "食品"),
                        "Sector33Code": company.get("sector33", "1000"),
                        "Sector33CodeName": company.get("sector33_name", "食品"),
                        "ScaleCategory": company.get("scale", "TOPIX Mid400"),
                        "MarketCode": company.get("market", "0111"),
                        "MarketCodeName": company.get("market_name", "プライム")
                    }
                    for company in companies
                ]
            }
        
        @staticmethod
        def build_daily_quotes(quotes: list) -> dict:
            """日次株価レスポンスを構築"""
            return {
                "daily_quotes": [
                    {
                        "Date": quote.get("date", "2024-01-01"),
                        "Code": quote["code"],
                        "Open": quote.get("open", 1000.0),
                        "High": quote.get("high", 1050.0),
                        "Low": quote.get("low", 980.0),
                        "Close": quote.get("close", 1020.0),
                        "Volume": quote.get("volume", 1000000),
                        "TurnoverValue": quote.get("turnover", 1020000000.0),
                        "AdjustmentOpen": quote.get("adj_open", quote.get("open", 1000.0)),
                        "AdjustmentHigh": quote.get("adj_high", quote.get("high", 1050.0)),
                        "AdjustmentLow": quote.get("adj_low", quote.get("low", 980.0)),
                        "AdjustmentClose": quote.get("adj_close", quote.get("close", 1020.0)),
                        "AdjustmentVolume": quote.get("adj_volume", quote.get("volume", 1000000))
                    }
                    for quote in quotes
                ]
            }
        
        @staticmethod
        def build_error_response(status_code: int, message: str) -> dict:
            """エラーレスポンスを構築"""
            error_messages = {
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                429: "Too Many Requests",
                500: "Internal Server Error"
            }
            
            return {
                "error": {
                    "status": status_code,
                    "title": error_messages.get(status_code, "Error"),
                    "detail": message
                }
            }
    
    return ResponseBuilder()


@pytest.fixture
def mock_external_api_calls():
    """
    外部API呼び出しを一括でモック化するフィクスチャ
    
    複数の外部APIを同時にモック化します。
    """
    mocks = {}
    
    # J-Quants API
    jquants_mock = AsyncMock()
    mocks["jquants"] = jquants_mock
    
    # その他の外部API（将来の拡張用）
    # mocks["other_api"] = AsyncMock()
    
    with patch("app.external_api.jquants_client.JQuantsClient", return_value=jquants_mock):
        yield mocks


@pytest.fixture
def rate_limit_simulator():
    """
    レート制限のシミュレーションを行うフィクスチャ
    
    API呼び出しのレート制限をテストする際に使用します。
    """
    class RateLimitSimulator:
        def __init__(self):
            self.call_count = 0
            self.rate_limit = 10
            self.reset_time = None
        
        async def simulate_call(self):
            """API呼び出しをシミュレート"""
            self.call_count += 1
            
            if self.call_count > self.rate_limit:
                # レート制限エラーを発生
                response = Mock()
                response.status_code = 429
                response.json.return_value = {
                    "error": "Rate limit exceeded",
                    "retry_after": 60
                }
                raise httpx.HTTPStatusError(
                    "Too Many Requests",
                    request=Mock(),
                    response=response
                )
            
            return {"status": "success", "call_number": self.call_count}
        
        def reset(self):
            """カウンターをリセット"""
            self.call_count = 0
            self.reset_time = datetime.utcnow()
    
    return RateLimitSimulator()


@pytest.fixture
def api_response_validator():
    """
    APIレスポンスの検証ヘルパーを提供するフィクスチャ
    """
    class ResponseValidator:
        @staticmethod
        def validate_company_response(response: dict) -> bool:
            """企業情報レスポンスの検証"""
            required_fields = ["Code", "CompanyName", "MarketCode"]
            
            if "info" not in response:
                return False
            
            for company in response["info"]:
                for field in required_fields:
                    if field not in company:
                        return False
            
            return True
        
        @staticmethod
        def validate_quote_response(response: dict) -> bool:
            """株価レスポンスの検証"""
            required_fields = ["Date", "Code", "Open", "High", "Low", "Close", "Volume"]
            
            if "daily_quotes" not in response:
                return False
            
            for quote in response["daily_quotes"]:
                for field in required_fields:
                    if field not in quote:
                        return False
            
            return True
    
    return ResponseValidator()


@pytest.fixture
def mock_token_manager():
    """
    トークン管理のモックを提供するフィクスチャ
    """
    mock = Mock()
    
    # 有効なトークンを返す
    mock.get_valid_token = AsyncMock(return_value="valid_id_token_123456")
    mock.refresh_tokens = AsyncMock(return_value={
        "id_token": "new_id_token_123456",
        "refresh_token": "new_refresh_token_123456"
    })
    mock.is_token_expired = Mock(return_value=False)
    mock.save_tokens = AsyncMock()
    
    return mock