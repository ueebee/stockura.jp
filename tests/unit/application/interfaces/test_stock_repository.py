"""Unit tests for StockRepositoryInterface."""
import pytest
from unittest.mock import AsyncMock, Mock
from typing import List, Optional

from app.application.interfaces.repositories.stock_repository import StockRepositoryInterface
from app.domain.entities.stock import Stock, StockCode, MarketCode, SectorCode17, SectorCode33
from app.domain.value_objects.ticker_symbol import TickerSymbol


class MockStockRepository(StockRepositoryInterface):
    """Mock implementation of StockRepositoryInterface for testing."""
    
    def __init__(self):
        super().__init__()
        self._find_by_id = AsyncMock()
        self._find_by_ticker = AsyncMock()
        self._find_all = AsyncMock()
        self._save = AsyncMock()
        self._delete = AsyncMock()
        self._exists = AsyncMock()
        self._count = AsyncMock()
        self._search = AsyncMock()
        self._find_by_market = AsyncMock()
        self._update_market_cap = AsyncMock()
    
    async def find_by_id(self, stock_id: int) -> Optional[Stock]:
        return await self._find_by_id(stock_id)
    
    async def find_by_ticker(self, ticker_symbol: TickerSymbol) -> Optional[Stock]:
        return await self._find_by_ticker(ticker_symbol)
    
    async def find_all(self, market: Optional[str] = None, sector: Optional[str] = None, 
                       limit: int = 100, offset: int = 0) -> List[Stock]:
        return await self._find_all(market=market, sector=sector, limit=limit, offset=offset)
    
    async def save(self, stock: Stock) -> Stock:
        return await self._save(stock)
    
    async def delete(self, stock_id: int) -> bool:
        return await self._delete(stock_id)
    
    async def exists(self, ticker_symbol: TickerSymbol) -> bool:
        return await self._exists(ticker_symbol)
    
    async def count(self, market: Optional[str] = None, sector: Optional[str] = None) -> int:
        return await self._count(market=market, sector=sector)
    
    async def search(self, query: str, limit: int = 10) -> List[Stock]:
        return await self._search(query, limit=limit)
    
    async def find_by_market(self, market: str) -> List[Stock]:
        return await self._find_by_market(market)
    
    async def update_market_cap(self, ticker_symbol: TickerSymbol, market_cap: float) -> bool:
        return await self._update_market_cap(ticker_symbol, market_cap)


class TestStockRepositoryInterface:
    """Test cases for StockRepositoryInterface."""
    
    @pytest.fixture
    def repository(self):
        """Create mock repository instance."""
        return MockStockRepository()
    
    @pytest.fixture
    def sample_stock(self):
        """Create sample stock entity."""
        return Stock(
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english="Toyota Motor Corporation",
            sector_17_code=SectorCode17.AUTOMOBILES_TRANSPORTATION,
            sector_17_name="自動車・輸送機",
            sector_33_code=SectorCode33.TRANSPORTATION_EQUIPMENT,
            sector_33_name="輸送用機器",
            scale_category="1",
            market_code=MarketCode.PRIME,
            market_name="プライム市場"
        )
    
    # find_by_id tests
    @pytest.mark.asyncio
    async def test_find_by_id_found(self, repository, sample_stock):
        """Test finding stock by ID when found."""
        # Arrange
        stock_id = 123
        repository._find_by_id.return_value = sample_stock
        
        # Act
        result = await repository.find_by_id(stock_id)
        
        # Assert
        assert result == sample_stock
        assert result.code.value == "7203"
        repository._find_by_id.assert_called_once_with(stock_id)
    
    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository):
        """Test finding stock by ID when not found."""
        # Arrange
        stock_id = 999
        repository._find_by_id.return_value = None
        
        # Act
        result = await repository.find_by_id(stock_id)
        
        # Assert
        assert result is None
        repository._find_by_id.assert_called_once_with(stock_id)
    
    # find_by_ticker tests
    @pytest.mark.asyncio
    async def test_find_by_ticker_found(self, repository, sample_stock):
        """Test finding stock by ticker when found."""
        # Arrange
        ticker = TickerSymbol("7203")
        repository._find_by_ticker.return_value = sample_stock
        
        # Act
        result = await repository.find_by_ticker(ticker)
        
        # Assert
        assert result == sample_stock
        assert result.company_name == "トヨタ自動車"
        repository._find_by_ticker.assert_called_once_with(ticker)
    
    @pytest.mark.asyncio
    async def test_find_by_ticker_not_found(self, repository):
        """Test finding stock by ticker when not found."""
        # Arrange
        ticker = TickerSymbol("9999")
        repository._find_by_ticker.return_value = None
        
        # Act
        result = await repository.find_by_ticker(ticker)
        
        # Assert
        assert result is None
        repository._find_by_ticker.assert_called_once_with(ticker)
    
    # find_all tests
    @pytest.mark.asyncio
    async def test_find_all_no_filters(self, repository):
        """Test finding all stocks without filters."""
        # Arrange
        stocks = [
            Stock(
                code=StockCode(f"{1000+i}"),
                company_name=f"Company {i}",
                company_name_english=f"Company {i} Inc.",
                sector_17_code=None,
                sector_17_name=None,
                sector_33_code=None,
                sector_33_name=None,
                scale_category="1",
                market_code=MarketCode.PRIME,
                market_name="プライム市場"
            )
            for i in range(3)
        ]
        repository._find_all.return_value = stocks
        
        # Act
        result = await repository.find_all()
        
        # Assert
        assert len(result) == 3
        assert result[0].code.value == "1000"
        repository._find_all.assert_called_once_with(market=None, sector=None, limit=100, offset=0)
    
    @pytest.mark.asyncio
    async def test_find_all_with_filters(self, repository):
        """Test finding all stocks with market and sector filters."""
        # Arrange
        stocks = []
        repository._find_all.return_value = stocks
        
        # Act
        result = await repository.find_all(market="プライム", sector="情報・通信", limit=50, offset=10)
        
        # Assert
        assert result == []
        repository._find_all.assert_called_once_with(
            market="プライム", sector="情報・通信", limit=50, offset=10
        )
    
    # save tests
    @pytest.mark.asyncio
    async def test_save_new_stock(self, repository, sample_stock):
        """Test saving a new stock."""
        # Arrange
        repository._save.return_value = sample_stock
        
        # Act
        result = await repository.save(sample_stock)
        
        # Assert
        assert result == sample_stock
        repository._save.assert_called_once_with(sample_stock)
    
    @pytest.mark.asyncio
    async def test_save_existing_stock(self, repository, sample_stock):
        """Test updating an existing stock."""
        # Arrange
        updated_stock = sample_stock
        repository._save.return_value = updated_stock
        
        # Act
        result = await repository.save(updated_stock)
        
        # Assert
        assert result == updated_stock
        repository._save.assert_called_once()
    
    # delete tests
    @pytest.mark.asyncio
    async def test_delete_existing_stock(self, repository):
        """Test deleting an existing stock."""
        # Arrange
        stock_id = 123
        repository._delete.return_value = True
        
        # Act
        result = await repository.delete(stock_id)
        
        # Assert
        assert result is True
        repository._delete.assert_called_once_with(stock_id)
    
    @pytest.mark.asyncio
    async def test_delete_non_existing_stock(self, repository):
        """Test deleting a non-existing stock."""
        # Arrange
        stock_id = 999
        repository._delete.return_value = False
        
        # Act
        result = await repository.delete(stock_id)
        
        # Assert
        assert result is False
        repository._delete.assert_called_once_with(stock_id)
    
    # exists tests
    @pytest.mark.asyncio
    async def test_exists_true(self, repository):
        """Test checking existence when stock exists."""
        # Arrange
        ticker = TickerSymbol("7203")
        repository._exists.return_value = True
        
        # Act
        result = await repository.exists(ticker)
        
        # Assert
        assert result is True
        repository._exists.assert_called_once_with(ticker)
    
    @pytest.mark.asyncio
    async def test_exists_false(self, repository):
        """Test checking existence when stock doesn't exist."""
        # Arrange
        ticker = TickerSymbol("9999")
        repository._exists.return_value = False
        
        # Act
        result = await repository.exists(ticker)
        
        # Assert
        assert result is False
        repository._exists.assert_called_once_with(ticker)
    
    # count tests
    @pytest.mark.asyncio
    async def test_count_all(self, repository):
        """Test counting all stocks."""
        # Arrange
        repository._count.return_value = 3000
        
        # Act
        result = await repository.count()
        
        # Assert
        assert result == 3000
        repository._count.assert_called_once_with(market=None, sector=None)
    
    @pytest.mark.asyncio
    async def test_count_with_filters(self, repository):
        """Test counting stocks with filters."""
        # Arrange
        repository._count.return_value = 150
        
        # Act
        result = await repository.count(market="プライム", sector="情報・通信")
        
        # Assert
        assert result == 150
        repository._count.assert_called_once_with(market="プライム", sector="情報・通信")
    
    # search tests
    @pytest.mark.asyncio
    async def test_search_by_name(self, repository):
        """Test searching stocks by company name."""
        # Arrange
        query = "トヨタ"
        stocks = [
            Stock(
                code=StockCode("7203"),
                company_name="トヨタ自動車",
                company_name_english="Toyota Motor Corporation",
                sector_17_code=None,
                sector_17_name=None,
                sector_33_code=None,
                sector_33_name=None,
                scale_category="1",
                market_code=MarketCode.PRIME,
                market_name="プライム市場"
            )
        ]
        repository._search.return_value = stocks
        
        # Act
        result = await repository.search(query)
        
        # Assert
        assert len(result) == 1
        assert result[0].company_name == "トヨタ自動車"
        repository._search.assert_called_once_with(query, limit=10)
    
    @pytest.mark.asyncio
    async def test_search_with_custom_limit(self, repository):
        """Test searching stocks with custom limit."""
        # Arrange
        query = "銀行"
        limit = 20
        stocks = []
        repository._search.return_value = stocks
        
        # Act
        result = await repository.search(query, limit=limit)
        
        # Assert
        assert result == []
        repository._search.assert_called_once_with(query, limit=20)
    
    # find_by_market tests
    @pytest.mark.asyncio
    async def test_find_by_market(self, repository):
        """Test finding stocks by market."""
        # Arrange
        market = "プライム市場"
        stocks = [
            Stock(
                code=StockCode(f"{7000+i}"),
                company_name=f"Prime Company {i}",
                company_name_english=f"Prime Company {i} Inc.",
                sector_17_code=None,
                sector_17_name=None,
                sector_33_code=None,
                sector_33_name=None,
                scale_category="1",
                market_code=MarketCode.PRIME,
                market_name="プライム市場"
            )
            for i in range(5)
        ]
        repository._find_by_market.return_value = stocks
        
        # Act
        result = await repository.find_by_market(market)
        
        # Assert
        assert len(result) == 5
        assert all(s.market_name == "プライム市場" for s in result)
        repository._find_by_market.assert_called_once_with(market)
    
    # update_market_cap tests
    @pytest.mark.asyncio
    async def test_update_market_cap_success(self, repository):
        """Test updating market cap successfully."""
        # Arrange
        ticker = TickerSymbol("7203")
        market_cap = 35000000000000.0  # 35 trillion yen
        repository._update_market_cap.return_value = True
        
        # Act
        result = await repository.update_market_cap(ticker, market_cap)
        
        # Assert
        assert result is True
        repository._update_market_cap.assert_called_once_with(ticker, market_cap)
    
    @pytest.mark.asyncio
    async def test_update_market_cap_not_found(self, repository):
        """Test updating market cap when stock not found."""
        # Arrange
        ticker = TickerSymbol("9999")
        market_cap = 1000000000.0
        repository._update_market_cap.return_value = False
        
        # Act
        result = await repository.update_market_cap(ticker, market_cap)
        
        # Assert
        assert result is False
        repository._update_market_cap.assert_called_once_with(ticker, market_cap)
    
    # Interface compliance test
    def test_interface_implementation(self):
        """Test that MockStockRepository implements all interface methods."""
        # Arrange
        interface_methods = [
            'find_by_id',
            'find_by_ticker',
            'find_all',
            'save',
            'delete',
            'exists',
            'count',
            'search',
            'find_by_market',
            'update_market_cap'
        ]
        
        repository = MockStockRepository()
        
        # Assert
        for method_name in interface_methods:
            assert hasattr(repository, method_name), f"Missing method: {method_name}"
            method = getattr(repository, method_name)
            assert callable(method), f"Method {method_name} is not callable"
            # Check that the private mock also exists
            private_attr = f"_{method_name}"
            assert hasattr(repository, private_attr), f"Missing private mock: {private_attr}"
            assert isinstance(getattr(repository, private_attr), AsyncMock), f"{private_attr} is not an AsyncMock"