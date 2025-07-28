"""Unit tests for JQuantsStockRepository."""
import pytest
import json
from unittest.mock import AsyncMock, Mock, patch, mock_open
from datetime import date, datetime, timedelta
from pathlib import Path

from app.infrastructure.jquants.stock_repository_impl import JQuantsStockRepository
from app.domain.entities.stock import Stock, StockList, StockCode, MarketCode, SectorCode17, SectorCode33
from app.domain.entities.auth import JQuantsCredentials, IdToken, RefreshToken
from app.domain.exceptions.jquants_exceptions import (
    DataNotFoundError,
    NetworkError,
    StorageError,
    ValidationError,
)


class TestJQuantsStockRepository:
    """Test cases for JQuantsStockRepository."""
    
    @pytest.fixture
    def mock_auth_use_case(self):
        """Create mock auth use case."""
        mock = AsyncMock()
        test_credentials = JQuantsCredentials(
            email="test@example.com",
            password="test_password",
            id_token=IdToken(
                value="test_token",
                expires_at=datetime.now() + timedelta(hours=1)
            )
        )
        mock.ensure_valid_token = AsyncMock(return_value=test_credentials)
        return mock
    
    @pytest.fixture
    def credentials(self):
        """Create test credentials."""
        return JQuantsCredentials(
            email="test@example.com",
            password="test_password",
            id_token=IdToken(
                value="test_token",
                expires_at=datetime.now() + timedelta(hours=1)
            )
        )
    
    @pytest.fixture
    def repository(self, mock_auth_use_case, credentials, tmp_path):
        """Create repository instance."""
        return JQuantsStockRepository(
            auth_use_case=mock_auth_use_case,
            credentials=credentials,
            cache_dir=tmp_path / "cache"
        )
    
    @pytest.fixture
    def sample_stock_data(self):
        """Create sample stock data from API."""
        return [
            {
                "Code": "1234",
                "CompanyName": "テスト株式会社",
                "CompanyNameEnglish": "Test Corporation",
                "Sector17Code": "1",
                "Sector17CodeName": "食品",
                "Sector33Code": "0050",
                "Sector33CodeName": "水産・農林業",
                "ScaleCategory": "1",
                "MarketCode": "0101",
                "MarketCodeName": "プライム市場"
            },
            {
                "Code": "5678",
                "CompanyName": "サンプル工業",
                "CompanyNameEnglish": "Sample Industries",
                "Sector17Code": "8",
                "Sector17CodeName": "機械",
                "Sector33Code": "3600",
                "Sector33CodeName": "機械",
                "ScaleCategory": "2",
                "MarketCode": "0102",
                "MarketCodeName": "スタンダード市場"
            }
        ]
    
    # 基本機能テスト
    @pytest.mark.asyncio
    async def test_get_listed_stocks_success(self, repository, sample_stock_data):
        """Test successful retrieval of listed stocks."""
        # Arrange
        with patch('app.infrastructure.jquants.stock_repository_impl.JQuantsBaseClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_paginated = AsyncMock(return_value=sample_stock_data)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            result = await repository.get_listed_stocks()
            
            # Assert
            assert isinstance(result, StockList)
            assert len(result.stocks) == 2
            assert result.stocks[0].code.value == "1234"
            assert result.stocks[0].company_name == "テスト株式会社"
            assert result.stocks[1].code.value == "5678"
            assert result.updated_date == date.today()
    
    @pytest.mark.asyncio
    async def test_get_stock_by_code_found(self, repository, sample_stock_data):
        """Test getting stock by code when found."""
        # Arrange
        with patch('app.infrastructure.jquants.stock_repository_impl.JQuantsBaseClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_paginated = AsyncMock(return_value=[sample_stock_data[0]])
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            result = await repository.get_stock_by_code("1234")
            
            # Assert
            assert result is not None
            assert result.code.value == "1234"
            assert result.company_name == "テスト株式会社"
            mock_client.get_paginated.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_stock_by_code_not_found(self, repository):
        """Test getting stock by code when not found."""
        # Arrange
        with patch('app.infrastructure.jquants.stock_repository_impl.JQuantsBaseClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_paginated = AsyncMock(return_value=[])
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            result = await repository.get_stock_by_code("9999")
            
            # Assert
            assert result is None
    
    @pytest.mark.asyncio
    async def test_search_stocks_by_name(self, repository, sample_stock_data):
        """Test searching stocks by name."""
        # Arrange
        with patch('app.infrastructure.jquants.stock_repository_impl.JQuantsBaseClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_paginated = AsyncMock(return_value=sample_stock_data)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            result = await repository.search_stocks("テスト")
            
            # Assert
            assert len(result.stocks) == 1
            assert result.stocks[0].company_name == "テスト株式会社"
    
    # バリデーションテスト
    @pytest.mark.asyncio
    async def test_get_stock_by_code_invalid_code(self, repository):
        """Test getting stock with invalid code format."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await repository.get_stock_by_code("ABC1")
        
        assert "4 桁の数字" in str(exc_info.value)
    
    # キャッシュ機能テスト
    @pytest.mark.asyncio
    async def test_save_stock_list_to_cache(self, repository, tmp_path):
        """Test saving stock list to cache."""
        # Arrange
        stocks = [
            Stock(
                code=StockCode("1234"),
                company_name="テスト株式会社",
                company_name_english="Test Corporation",
                sector_17_code=SectorCode17.FOODS,
                sector_17_name="食品",
                sector_33_code=SectorCode33.FISHERY_AGRICULTURE_FORESTRY,
                sector_33_name="水産・農林業",
                scale_category="1",
                market_code=MarketCode.PRIME,
                market_name="プライム市場"
            )
        ]
        stock_list = StockList(stocks=stocks, updated_date=date.today())
        
        # Act
        await repository.save_stock_list(stock_list)
        
        # Assert
        cache_file = tmp_path / "cache" / "stock_list.json"
        assert cache_file.exists()
        
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert len(data["stocks"]) == 1
        assert data["stocks"][0]["Code"] == "1234"
        assert data["updated_date"] == date.today().isoformat()
    
    @pytest.mark.asyncio
    async def test_load_cached_stock_list(self, repository, tmp_path):
        """Test loading cached stock list."""
        # Arrange
        cache_data = {
            "updated_date": date.today().isoformat(),
            "stocks": [
                {
                    "Code": "1234",
                    "CompanyName": "テスト株式会社",
                    "CompanyNameEnglish": "Test Corporation",
                    "Sector17Code": "1",
                    "Sector17CodeName": "食品",
                    "Sector33Code": "0050",
                    "Sector33CodeName": "水産・農林業",
                    "ScaleCategory": "1",
                    "MarketCode": "0101",
                    "MarketCodeName": "プライム市場"
                }
            ]
        }
        
        cache_file = tmp_path / "cache" / "stock_list.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
        
        # Act
        result = await repository.load_cached_stock_list()
        
        # Assert
        assert result is not None
        assert len(result.stocks) == 1
        assert result.stocks[0].code.value == "1234"
        assert result.updated_date == date.today()
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, repository, tmp_path):
        """Test cache expiration by date."""
        # Arrange
        old_date = date(2023, 1, 1)
        cache_data = {
            "updated_date": old_date.isoformat(),
            "stocks": []
        }
        
        cache_file = tmp_path / "cache" / "stock_list.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
        
        # Act
        result = await repository.load_cached_stock_list(date=date.today())
        
        # Assert
        assert result is None  # Cache should not be used for different date
    
    # エラーハンドリング
    @pytest.mark.asyncio
    async def test_api_rate_limit_error(self, repository):
        """Test handling of API rate limit error."""
        # Arrange
        with patch('app.infrastructure.jquants.stock_repository_impl.JQuantsBaseClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_paginated = AsyncMock(side_effect=NetworkError("Rate limit exceeded"))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act & Assert
            with pytest.raises(NetworkError) as exc_info:
                await repository.get_listed_stocks()
            
            assert "Rate limit exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_network_timeout_error(self, repository):
        """Test handling of network timeout."""
        # Arrange
        with patch('app.infrastructure.jquants.stock_repository_impl.JQuantsBaseClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_paginated = AsyncMock(side_effect=Exception("Connection timeout"))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act & Assert
            with pytest.raises(NetworkError) as exc_info:
                await repository.get_listed_stocks()
            
            assert "エラーが発生しました" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_response_format(self, repository):
        """Test handling of invalid API response format."""
        # Arrange
        # Invalid data will cause Stock.from_dict to raise exception, which gets caught and skipped
        # Resulting in empty stocks list which triggers DataNotFoundError
        invalid_data = [{"invalid": "data"}]  # Missing required fields
        
        with patch('app.infrastructure.jquants.stock_repository_impl.JQuantsBaseClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_paginated = AsyncMock(return_value=invalid_data)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act & Assert
            with pytest.raises(DataNotFoundError) as exc_info:
                await repository.get_listed_stocks()
            
            assert "銘柄データが見つかりません" in str(exc_info.value)
    
    # 追加テスト: フィルタリング機能
    @pytest.mark.asyncio
    async def test_search_with_market_filter(self, repository, sample_stock_data):
        """Test searching stocks with market filter."""
        # Arrange
        with patch('app.infrastructure.jquants.stock_repository_impl.JQuantsBaseClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_paginated = AsyncMock(return_value=sample_stock_data)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            result = await repository.search_stocks("", market_code="0101")
            
            # Assert
            assert len(result.stocks) == 1
            assert result.stocks[0].market_code.value == "0101"
    
    @pytest.mark.asyncio
    async def test_search_with_sector_filter(self, repository, sample_stock_data):
        """Test searching stocks with sector filter."""
        # Arrange
        with patch('app.infrastructure.jquants.stock_repository_impl.JQuantsBaseClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_paginated = AsyncMock(return_value=sample_stock_data)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            result = await repository.search_stocks("", sector_17_code="1")
            
            # Assert
            assert len(result.stocks) == 1
            assert result.stocks[0].sector_17_code.value == "1"
    
    @pytest.mark.asyncio
    async def test_cache_file_not_found(self, repository):
        """Test loading cache when file doesn't exist."""
        # Act
        result = await repository.load_cached_stock_list()
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_save_cache_error(self, repository, tmp_path):
        """Test error handling when saving cache fails."""
        # Arrange
        stocks = [
            Stock(
                code=StockCode("1234"),
                company_name="テスト株式会社",
                company_name_english="Test Corporation",
                sector_17_code=SectorCode17.FOODS,
                sector_17_name="食品",
                sector_33_code=SectorCode33.FISHERY_AGRICULTURE_FORESTRY,
                sector_33_name="水産・農林業",
                scale_category="1",
                market_code=MarketCode.PRIME,
                market_name="プライム市場"
            )
        ]
        stock_list = StockList(stocks=stocks, updated_date=date.today())
        
        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Act & Assert
            with pytest.raises(StorageError) as exc_info:
                await repository.save_stock_list(stock_list)
            
            assert "保存に失敗しました" in str(exc_info.value)