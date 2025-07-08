"""
モデル関連のテストフィクスチャ

テストデータの生成、ファクトリー、サンプルデータセットを提供します。
"""
import pytest
import pytest_asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional
import random
from faker import Faker

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, DailyQuote, DataSource


# 日本語対応のFakerインスタンス
fake = Faker('ja_JP')


@pytest.fixture
def company_factory():
    """
    企業データのファクトリーフィクスチャ
    
    使用例:
        company = company_factory(code="12345", company_name="テスト株式会社")
    """
    def _factory(
        code: Optional[str] = None,
        company_name: Optional[str] = None,
        company_name_english: Optional[str] = None,
        market_code: Optional[str] = None,
        sector17_code: Optional[str] = None,
        sector33_code: Optional[str] = None,
        scale_category: Optional[str] = None,
        margin_code: Optional[str] = None,
        is_active: bool = True
    ) -> Company:
        
        return Company(
            code=code or f"{random.randint(1000, 9999)}",
            company_name=company_name or fake.company(),
            company_name_english=company_name_english or fake.company(),
            market_code=market_code or random.choice(["0101", "0102", "0104"]),
            sector17_code=sector17_code or str(random.randint(1, 17)),
            sector33_code=sector33_code or f"{random.randint(1000, 9999)}",
            scale_category=scale_category or random.choice(["TOPIX Core30", "TOPIX Large70", "TOPIX Mid400", "TOPIX Small"]),
            margin_code=margin_code,
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    return _factory


@pytest.fixture
def daily_quote_factory():
    """
    日次株価データのファクトリーフィクスチャ
    
    使用例:
        quote = daily_quote_factory(code="12345", date=date(2024, 1, 1))
    """
    def _factory(
        code: Optional[str] = None,
        date_: Optional[date] = None,
        open_: Optional[Decimal] = None,
        high: Optional[Decimal] = None,
        low: Optional[Decimal] = None,
        close: Optional[Decimal] = None,
        volume: Optional[int] = None,
        turnover_value: Optional[Decimal] = None,
        adjustment_open: Optional[Decimal] = None,
        adjustment_high: Optional[Decimal] = None,
        adjustment_low: Optional[Decimal] = None,
        adjustment_close: Optional[Decimal] = None,
        adjustment_volume: Optional[int] = None
    ) -> DailyQuote:
        
        # 基準価格を生成
        base_price = Decimal(str(random.randint(1000, 10000)))
        variation = Decimal(str(random.uniform(0.95, 1.05)))
        
        # デフォルト値の生成
        if open_ is None:
            open_ = base_price * variation
        if high is None:
            high = open_ * Decimal(str(random.uniform(1.0, 1.05)))
        if low is None:
            low = open_ * Decimal(str(random.uniform(0.95, 1.0)))
        if close is None:
            close = low + (high - low) * Decimal(str(random.random()))
        if volume is None:
            volume = random.randint(100000, 10000000)
        if turnover_value is None:
            turnover_value = close * Decimal(str(volume)) / Decimal("100")
        
        return DailyQuote(
            code=code or f"{random.randint(1000, 9999)}",
            date=date_ or date.today() - timedelta(days=random.randint(1, 365)),
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            turnover_value=turnover_value,
            adjustment_open=adjustment_open or open_,
            adjustment_high=adjustment_high or high,
            adjustment_low=adjustment_low or low,
            adjustment_close=adjustment_close or close,
            adjustment_volume=adjustment_volume or volume,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    return _factory


@pytest.fixture
def data_source_factory():
    """
    データソースのファクトリーフィクスチャ
    
    使用例:
        data_source = data_source_factory(name="テストデータソース")
    """
    def _factory(
        name: Optional[str] = None,
        description: Optional[str] = None,
        provider: str = "jquants",
        base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        credentials: Optional[dict] = None,
        is_active: bool = True,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000
    ) -> DataSource:
        
        return DataSource(
            name=name or f"Test Data Source {random.randint(1, 100)}",
            description=description or "テスト用のデータソース",
            provider=provider,
            base_url=base_url or "https://api.example.com",
            api_version=api_version or "v1",
            credentials_encrypted=credentials or {},
            is_active=is_active,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    return _factory


@pytest_asyncio.fixture
async def sample_companies(async_session: AsyncSession, company_factory):
    """
    サンプル企業データセットを作成するフィクスチャ
    
    よく使用する企業データのセットを提供します。
    """
    companies = [
        company_factory(code="72030", company_name="トヨタ自動車", market_code="0101"),
        company_factory(code="67580", company_name="ソニーグループ", market_code="0101"),
        company_factory(code="86060", company_name="日立製作所", market_code="0101"),
        company_factory(code="45020", company_name="武田薬品工業", market_code="0101"),
        company_factory(code="90200", company_name="東日本旅客鉄道", market_code="0101"),
    ]
    
    for company in companies:
        async_session.add(company)
    
    await async_session.commit()
    return companies


@pytest_asyncio.fixture
async def sample_daily_quotes(
    async_session: AsyncSession,
    sample_companies: List[Company],
    daily_quote_factory
):
    """
    サンプル株価データセットを作成するフィクスチャ
    
    サンプル企業に対する30日分の株価データを生成します。
    """
    quotes = []
    base_date = date.today()
    
    for company in sample_companies:
        for i in range(30):
            quote_date = base_date - timedelta(days=i)
            quote = daily_quote_factory(
                code=company.code,
                date_=quote_date
            )
            quotes.append(quote)
            async_session.add(quote)
    
    await async_session.commit()
    return quotes


@pytest.fixture
def mock_jquants_response_data():
    """
    J-Quants APIのモックレスポンスデータを提供するフィクスチャ
    """
    return {
        "listed_info": {
            "info": [
                {
                    "Date": "2024-01-01",
                    "Code": "72030",
                    "CompanyName": "トヨタ自動車",
                    "CompanyNameEnglish": "TOYOTA MOTOR CORPORATION",
                    "Sector17Code": "16",
                    "Sector17CodeName": "輸送用機器",
                    "Sector33Code": "3050",
                    "Sector33CodeName": "自動車",
                    "ScaleCategory": "TOPIX Core30",
                    "MarketCode": "0111",
                    "MarketCodeName": "プライム"
                }
            ]
        },
        "daily_quotes": {
            "daily_quotes": [
                {
                    "Date": "2024-01-01",
                    "Code": "72030",
                    "Open": 2500.0,
                    "High": 2550.0,
                    "Low": 2480.0,
                    "Close": 2520.0,
                    "Volume": 15000000,
                    "TurnoverValue": 37800000000.0,
                    "AdjustmentOpen": 2500.0,
                    "AdjustmentHigh": 2550.0,
                    "AdjustmentLow": 2480.0,
                    "AdjustmentClose": 2520.0,
                    "AdjustmentVolume": 15000000
                }
            ]
        },
        "refresh_token": {
            "refreshToken": "new_refresh_token_123456"
        },
        "id_token": {
            "idToken": "new_id_token_123456"
        }
    }


@pytest.fixture
def assert_model_fields():
    """
    モデルフィールドの検証ヘルパーを提供するフィクスチャ
    """
    class ModelFieldAssertions:
        @staticmethod
        def assert_company_fields(company: Company, expected: dict):
            """企業モデルのフィールドを検証"""
            for field, value in expected.items():
                assert getattr(company, field) == value, f"Company.{field} mismatch"
            
            # 必須フィールドの存在確認
            assert company.id is not None
            assert company.created_at is not None
            assert company.updated_at is not None
        
        @staticmethod
        def assert_daily_quote_fields(quote: DailyQuote, expected: dict):
            """株価モデルのフィールドを検証"""
            for field, value in expected.items():
                actual = getattr(quote, field)
                if isinstance(value, Decimal):
                    assert actual == value, f"DailyQuote.{field} mismatch: {actual} != {value}"
                else:
                    assert actual == value, f"DailyQuote.{field} mismatch"
            
            # 必須フィールドの存在確認
            assert quote.id is not None
            assert quote.created_at is not None
            assert quote.updated_at is not None
    
    return ModelFieldAssertions()