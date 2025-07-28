"""Unit tests for AnalyzeStockUseCase."""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import date

from app.application.use_cases.analyze_stock import AnalyzeStockUseCase
from app.domain.entities.stock import Stock
from app.domain.entities.price import Price
from app.domain.exceptions.stock_exceptions import StockNotFoundError, InsufficientDataError
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.value_objects.time_period import TimePeriod
from tests.mocks.jquants_mock import MockJQuantsClient, MockYFinanceClient
from tests.factories.price_factory import PriceFactory


class TestAnalyzeStockUseCase:
    """Test cases for AnalyzeStockUseCase."""
    
    @pytest.fixture
    def mock_stock_repository(self):
        """Create mock stock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_price_calculator(self):
        """Create mock price calculator."""
        mock = Mock()
        mock.calculate_sma = Mock(return_value=1000.0)
        mock.calculate_ema = Mock(return_value=1010.0)
        mock.calculate_rsi = Mock(return_value=50.0)
        mock.calculate_volatility = Mock(return_value=0.02)
        mock.identify_support_resistance = Mock(return_value={
            "support": [950.0, 900.0],
            "resistance": [1050.0, 1100.0]
        })
        return mock
    
    @pytest.fixture
    def use_case(self, mock_stock_repository, mock_price_calculator):
        """Create use case instance."""
        jquants_client = MockJQuantsClient()
        yfinance_client = MockYFinanceClient()
        
        return AnalyzeStockUseCase(
            stock_repository=mock_stock_repository,
            jquants_client=jquants_client,
            yfinance_client=yfinance_client,
            price_calculator=mock_price_calculator
        )
    
    @pytest.fixture
    def sample_stock(self):
        """Create sample stock."""
        from app.domain.entities.stock import StockCode, MarketCode, SectorCode17, SectorCode33
        
        return Stock(
            code=StockCode("1234"),
            company_name="Test Company",
            company_name_english="Test Company Ltd.",
            sector_17_code=SectorCode17.FOODS,
            sector_17_name="食品",
            sector_33_code=SectorCode33.FISHERY_AGRICULTURE_FORESTRY,
            sector_33_name="水産・農林業",
            scale_category="1",
            market_code=MarketCode.PRIME,
            market_name="プライム市場"
        )
    
    # 正常系テストケース
    @pytest.mark.asyncio
    async def test_analyze_with_valid_stock_code(self, use_case, mock_stock_repository, sample_stock):
        """Test analysis with valid stock code."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.stock.company_name == "Test Company"
        assert result.current_price is not None
        assert result.sma_20 == 1000.0
        assert result.sma_50 == 1000.0
        assert result.ema_20 == 1010.0
        assert result.rsi_14 == 50.0
        assert result.volatility_20 == 0.02
        assert len(result.support_levels) == 2
        assert len(result.resistance_levels) == 2
        assert result.recommendation == "HOLD - Mixed signals"
    
    @pytest.mark.asyncio
    async def test_analyze_with_custom_period(self, use_case, mock_stock_repository, sample_stock):
        """Test analysis with custom period."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        
        # Act
        result = await use_case.execute("1234", days=200)
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.current_price is not None
    
    @pytest.mark.asyncio
    async def test_generate_buy_recommendation(self, use_case, mock_stock_repository, sample_stock, mock_price_calculator):
        """Test generating BUY recommendation."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        # Set up indicators for bullish signal
        mock_price_calculator.calculate_sma = Mock(side_effect=[1000.0, 950.0])  # SMA20 > SMA50
        mock_price_calculator.calculate_rsi = Mock(return_value=25.0)  # Oversold
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert "BUY" in result.recommendation
        assert "oversold" in result.recommendation.lower()
    
    @pytest.mark.asyncio
    async def test_generate_sell_recommendation(self, use_case, mock_stock_repository, sample_stock, mock_price_calculator):
        """Test generating SELL recommendation."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        # Set up indicators for bearish signal
        mock_price_calculator.calculate_sma = Mock(side_effect=[950.0, 1000.0])  # SMA20 < SMA50
        mock_price_calculator.calculate_rsi = Mock(return_value=75.0)  # Overbought
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert "SELL" in result.recommendation
        assert "overbought" in result.recommendation.lower()
    
    @pytest.mark.asyncio
    async def test_generate_hold_recommendation(self, use_case, mock_stock_repository, sample_stock):
        """Test generating HOLD recommendation."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert "HOLD" in result.recommendation
    
    # 異常系テストケース
    @pytest.mark.asyncio
    async def test_analyze_with_invalid_stock_code(self, use_case, mock_stock_repository):
        """Test analysis with invalid stock code."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = None
        use_case._jquants_client = MockJQuantsClient(scenario="not_found")
        
        # Act & Assert
        with pytest.raises(StockNotFoundError) as exc_info:
            await use_case.execute("9999")
        
        assert "9999" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_with_no_price_data(self, use_case, mock_stock_repository, sample_stock):
        """Test analysis when no price data available."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        use_case._jquants_client = MockJQuantsClient(scenario="not_found")
        
        # Act & Assert
        with pytest.raises(InsufficientDataError) as exc_info:
            await use_case.execute("1234")
        
        assert exc_info.value.required == 20
        assert exc_info.value.available == 0
    
    @pytest.mark.asyncio
    async def test_analyze_with_partial_data(self, use_case, mock_stock_repository, sample_stock):
        """Test analysis with insufficient price data."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        use_case._jquants_client = MockJQuantsClient(scenario="insufficient_data")
        
        # Act & Assert
        with pytest.raises(InsufficientDataError) as exc_info:
            await use_case.execute("1234")
        
        assert exc_info.value.required == 20
        assert exc_info.value.available == 10
    
    @pytest.mark.asyncio
    async def test_analyze_with_api_error(self, use_case, mock_stock_repository):
        """Test analysis when API returns error."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = None
        use_case._jquants_client = MockJQuantsClient(scenario="error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await use_case.execute("1234")
        
        assert "Mock API error" in str(exc_info.value)
    
    # エッジケーステスト
    @pytest.mark.asyncio
    async def test_analyze_with_extreme_volatility(self, use_case, mock_stock_repository, sample_stock, mock_price_calculator):
        """Test analysis with extreme price volatility."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        mock_price_calculator.calculate_volatility = Mock(return_value=0.5)  # 50% volatility
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert result.volatility_20 == 0.5
        assert result.recommendation is not None
    
    @pytest.mark.asyncio
    async def test_analyze_with_zero_volume(self, use_case, mock_stock_repository, sample_stock):
        """Test analysis with zero trading volume."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        # Price factory will create prices with normal volume by default
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert result.current_price is not None
    
    # 追加テスト: データソース切り替え
    @pytest.mark.asyncio
    async def test_analyze_with_yfinance_source(self, use_case, mock_stock_repository, sample_stock):
        """Test analysis using yfinance as data source."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        
        # Act
        result = await use_case.execute("1234", source="yfinance")
        
        # Assert
        assert result.stock.ticker_symbol == "1234"
        assert use_case._yfinance_client.call_count > 0
    
    @pytest.mark.asyncio
    async def test_stock_saved_when_not_in_repository(self, use_case, mock_stock_repository):
        """Test that stock is saved to repository when not found."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = None
        from app.domain.entities.stock import StockCode, MarketCode, SectorCode17, SectorCode33
        
        mock_stock_repository.save.return_value = Stock(
            code=StockCode("1234"),
            company_name="Saved Company",
            company_name_english="Saved Company Ltd.",
            sector_17_code=SectorCode17.FOODS,
            sector_17_name="食品",
            sector_33_code=SectorCode33.FISHERY_AGRICULTURE_FORESTRY,
            sector_33_name="水産・農林業",
            scale_category="1",
            market_code=MarketCode.PRIME,
            market_name="プライム市場"
        )
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        mock_stock_repository.save.assert_called_once()
        assert result.stock.company_name == "Saved Company"
    
    @pytest.mark.asyncio
    async def test_handle_missing_technical_indicators(self, use_case, mock_stock_repository, sample_stock, mock_price_calculator):
        """Test handling when some technical indicators cannot be calculated."""
        # Arrange
        mock_stock_repository.find_by_ticker.return_value = sample_stock
        mock_price_calculator.calculate_sma = Mock(side_effect=[1000.0, InsufficientDataError(50, 30, "SMA")])
        mock_price_calculator.calculate_ema = Mock(side_effect=InsufficientDataError(20, 10, "EMA"))
        mock_price_calculator.calculate_rsi = Mock(side_effect=InsufficientDataError(14, 10, "RSI"))
        
        # Act
        result = await use_case.execute("1234")
        
        # Assert
        assert result.sma_20 == 1000.0
        assert result.sma_50 is None
        assert result.ema_20 is None
        assert result.rsi_14 is None
        assert result.recommendation in ["HOLD - Mixed signals", "BUY - Bullish technical indicators"]  # Should still generate recommendation