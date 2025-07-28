"""Unit tests for stock DTOs."""
import pytest
from datetime import datetime, date
from decimal import Decimal

from app.application.dtos.stock_dto import (
    StockDTO,
    PriceDTO,
    StockPriceDTO,
    PriceHistoryDTO,
    StockAnalysisDTO,
    MarketOverviewDTO,
    SearchResultDTO,
    CreateStockDTO,
    UpdateStockDTO,
)
from app.domain.entities.stock import Stock, StockCode, MarketCode, SectorCode17, SectorCode33
from app.domain.entities.price import Price
from app.domain.value_objects.ticker_symbol import TickerSymbol


class TestStockDTO:
    """Test cases for StockDTO."""
    
    def test_stock_dto_creation(self):
        """Test creating a StockDTO instance."""
        # Arrange
        now = datetime.now()
        
        # Act
        dto = StockDTO(
            id=1,
            ticker_symbol="1234",
            company_name="Test Corp",
            market="東証プライム",
            sector="情報・通信",
            industry="情報サービス",
            market_cap=1000000000.0,
            description="Test company",
            created_at=now,
            updated_at=now,
        )
        
        # Assert
        assert dto.id == 1
        assert dto.ticker_symbol == "1234"
        assert dto.company_name == "Test Corp"
        assert dto.market == "東証プライム"
        assert dto.sector == "情報・通信"
        assert dto.industry == "情報サービス"
        assert dto.market_cap == 1000000000.0
        assert dto.description == "Test company"
        assert dto.created_at == now
        assert dto.updated_at == now
    
    def test_stock_dto_from_entity(self):
        """Test creating StockDTO from Stock entity."""
        # Arrange
        stock = Stock(
            code=StockCode("1234"),
            company_name="テスト株式会社",
            company_name_english="Test Corporation",
            sector_17_code=SectorCode17.IT_COMMUNICATIONS_SERVICES,
            sector_17_name="情報・通信",
            sector_33_code=SectorCode33.INFORMATION_COMMUNICATION,
            sector_33_name="情報サービス",
            scale_category="1",
            market_code=MarketCode.PRIME,
            market_name="プライム市場"
        )
        
        # Act
        dto = StockDTO.from_entity(stock)
        
        # Assert
        assert dto.id is None
        assert dto.ticker_symbol == "1234"
        assert dto.company_name == "テスト株式会社"
        assert dto.market == "プライム市場"
        assert dto.sector == "情報・通信"
        assert dto.industry == "情報サービス"
        assert dto.market_cap is None
        assert dto.description is None
        assert dto.created_at is None
        assert dto.updated_at is None
    
    def test_stock_dto_from_entity_with_missing_fields(self):
        """Test creating StockDTO from entity with missing optional fields."""
        # Arrange
        stock = Stock(
            code=StockCode("5678"),
            company_name="ミニマル株式会社",
            company_name_english="Minimal Corp",
            sector_17_code=None,
            sector_17_name=None,
            sector_33_code=None,
            sector_33_name=None,
            scale_category="2",
            market_code=MarketCode.STANDARD,
            market_name=None
        )
        
        # Act
        dto = StockDTO.from_entity(stock)
        
        # Assert
        assert dto.ticker_symbol == "5678"
        assert dto.company_name == "ミニマル株式会社"
        assert dto.market == ""  # Default when market_name is None
        assert dto.sector is None
        assert dto.industry is None


class TestPriceDTO:
    """Test cases for PriceDTO."""
    
    def test_price_dto_creation(self):
        """Test creating a PriceDTO instance."""
        # Arrange
        timestamp = datetime.now()
        created_at = datetime.now()
        
        # Act
        dto = PriceDTO(
            id=1,
            ticker_symbol="1234",
            timestamp=timestamp,
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000000,
            adjusted_close=103.5,
            created_at=created_at,
        )
        
        # Assert
        assert dto.id == 1
        assert dto.ticker_symbol == "1234"
        assert dto.timestamp == timestamp
        assert dto.open == 100.0
        assert dto.high == 105.0
        assert dto.low == 98.0
        assert dto.close == 103.0
        assert dto.volume == 1000000
        assert dto.adjusted_close == 103.5
        assert dto.created_at == created_at
    
    def test_price_dto_from_entity_with_timestamp(self):
        """Test creating PriceDTO from Price entity with timestamp."""
        # Arrange
        now = datetime.now()
        price = Price(
            ticker_symbol=TickerSymbol("1234"),
            date=date.today(),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000000,
            adjusted_close=103.5,
            timestamp=now
        )
        
        # Act
        dto = PriceDTO.from_entity(price)
        
        # Assert
        assert dto.id is None
        assert dto.ticker_symbol == "1234"
        assert dto.timestamp == now
        assert dto.open == 100.0
        assert dto.high == 105.0
        assert dto.low == 98.0
        assert dto.close == 103.0
        assert dto.volume == 1000000
        assert dto.adjusted_close == 103.5
        assert dto.created_at is None
    
    def test_price_dto_from_entity_without_timestamp(self):
        """Test creating PriceDTO from Price entity without timestamp."""
        # Arrange
        test_date = date(2023, 1, 1)
        price = Price(
            ticker_symbol=TickerSymbol("5678"),
            date=test_date,
            open=200.0,
            high=210.0,
            low=195.0,
            close=205.0,
            volume=500000
        )
        
        # Act
        dto = PriceDTO.from_entity(price)
        
        # Assert
        assert dto.ticker_symbol == "5678"
        assert dto.timestamp == datetime(2023, 1, 1, 0, 0)
        assert dto.open == 200.0
        assert dto.high == 210.0
        assert dto.low == 195.0
        assert dto.close == 205.0
        assert dto.volume == 500000
        assert dto.adjusted_close is None


class TestStockPriceDTO:
    """Test cases for StockPriceDTO."""
    
    def test_stock_price_dto_creation(self):
        """Test creating a StockPriceDTO instance."""
        # Arrange
        stock_dto = StockDTO(
            id=1,
            ticker_symbol="1234",
            company_name="Test Corp",
            market="東証プライム",
            sector=None,
            industry=None,
            market_cap=None,
            description=None,
            created_at=None,
            updated_at=None,
        )
        
        price_dto = PriceDTO(
            id=1,
            ticker_symbol="1234",
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000000,
            adjusted_close=None,
            created_at=None,
        )
        
        # Act
        dto = StockPriceDTO(
            stock=stock_dto,
            current_price=price_dto,
            price_change=3.0,
            price_change_percent=3.0,
            volume_average=950000.0
        )
        
        # Assert
        assert dto.stock == stock_dto
        assert dto.current_price == price_dto
        assert dto.price_change == 3.0
        assert dto.price_change_percent == 3.0
        assert dto.volume_average == 950000.0
    
    def test_stock_price_dto_with_none_values(self):
        """Test StockPriceDTO with None values."""
        # Arrange
        stock_dto = StockDTO(
            id=None,
            ticker_symbol="9999",
            company_name="No Price Corp",
            market="東証グロース",
            sector=None,
            industry=None,
            market_cap=None,
            description=None,
            created_at=None,
            updated_at=None,
        )
        
        # Act
        dto = StockPriceDTO(
            stock=stock_dto,
            current_price=None,
            price_change=None,
            price_change_percent=None,
            volume_average=None
        )
        
        # Assert
        assert dto.stock == stock_dto
        assert dto.current_price is None
        assert dto.price_change is None
        assert dto.price_change_percent is None
        assert dto.volume_average is None


class TestPriceHistoryDTO:
    """Test cases for PriceHistoryDTO."""
    
    def test_price_history_dto_creation(self):
        """Test creating a PriceHistoryDTO instance."""
        # Arrange
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 31)
        prices = [
            PriceDTO(
                id=i,
                ticker_symbol="1234",
                timestamp=datetime(2023, 1, i),
                open=100.0 + i,
                high=105.0 + i,
                low=98.0 + i,
                close=103.0 + i,
                volume=1000000 + i * 10000,
                adjusted_close=None,
                created_at=None,
            )
            for i in range(1, 4)
        ]
        
        # Act
        dto = PriceHistoryDTO(
            ticker_symbol="1234",
            period_start=start,
            period_end=end,
            prices=prices,
            highest_price=108.0,
            lowest_price=99.0,
            average_volume=1010000.0
        )
        
        # Assert
        assert dto.ticker_symbol == "1234"
        assert dto.period_start == start
        assert dto.period_end == end
        assert len(dto.prices) == 3
        assert dto.highest_price == 108.0
        assert dto.lowest_price == 99.0
        assert dto.average_volume == 1010000.0


class TestStockAnalysisDTO:
    """Test cases for StockAnalysisDTO."""
    
    def test_stock_analysis_dto_creation(self):
        """Test creating a StockAnalysisDTO instance."""
        # Arrange
        stock_dto = StockDTO(
            id=1,
            ticker_symbol="1234",
            company_name="Analysis Corp",
            market="東証プライム",
            sector="情報・通信",
            industry="情報サービス",
            market_cap=None,
            description=None,
            created_at=None,
            updated_at=None,
        )
        
        # Act
        dto = StockAnalysisDTO(
            stock=stock_dto,
            current_price=103.0,
            sma_20=101.5,
            sma_50=99.8,
            ema_20=102.1,
            rsi_14=65.5,
            volatility_20=0.25,
            support_levels=[95.0, 90.0, 85.0],
            resistance_levels=[105.0, 110.0, 115.0],
            recommendation="BUY"
        )
        
        # Assert
        assert dto.stock == stock_dto
        assert dto.current_price == 103.0
        assert dto.sma_20 == 101.5
        assert dto.sma_50 == 99.8
        assert dto.ema_20 == 102.1
        assert dto.rsi_14 == 65.5
        assert dto.volatility_20 == 0.25
        assert dto.support_levels == [95.0, 90.0, 85.0]
        assert dto.resistance_levels == [105.0, 110.0, 115.0]
        assert dto.recommendation == "BUY"
    
    def test_stock_analysis_dto_with_none_values(self):
        """Test StockAnalysisDTO with None values."""
        # Arrange
        stock_dto = StockDTO(
            id=None,
            ticker_symbol="0000",
            company_name="No Analysis Corp",
            market="Unknown",
            sector=None,
            industry=None,
            market_cap=None,
            description=None,
            created_at=None,
            updated_at=None,
        )
        
        # Act
        dto = StockAnalysisDTO(
            stock=stock_dto,
            current_price=None,
            sma_20=None,
            sma_50=None,
            ema_20=None,
            rsi_14=None,
            volatility_20=None,
            support_levels=[],
            resistance_levels=[],
            recommendation=None
        )
        
        # Assert
        assert dto.stock == stock_dto
        assert dto.current_price is None
        assert dto.sma_20 is None
        assert dto.sma_50 is None
        assert dto.ema_20 is None
        assert dto.rsi_14 is None
        assert dto.volatility_20 is None
        assert dto.support_levels == []
        assert dto.resistance_levels == []
        assert dto.recommendation is None


class TestMarketOverviewDTO:
    """Test cases for MarketOverviewDTO."""
    
    def test_market_overview_dto_creation(self):
        """Test creating a MarketOverviewDTO instance."""
        # Arrange
        stock_dto = StockDTO(
            id=1,
            ticker_symbol="1234",
            company_name="Active Corp",
            market="東証プライム",
            sector=None,
            industry=None,
            market_cap=None,
            description=None,
            created_at=None,
            updated_at=None,
        )
        
        stock_price_dto = StockPriceDTO(
            stock=stock_dto,
            current_price=None,
            price_change=5.0,
            price_change_percent=5.0,
            volume_average=None
        )
        
        # Act
        dto = MarketOverviewDTO(
            market_name="東証プライム",
            total_stocks=2170,
            advancing=1200,
            declining=800,
            unchanged=170,
            total_volume=3000000000,
            market_cap=750000000000000.0,
            top_gainers=[stock_price_dto],
            top_losers=[],
            most_active=[stock_price_dto]
        )
        
        # Assert
        assert dto.market_name == "東証プライム"
        assert dto.total_stocks == 2170
        assert dto.advancing == 1200
        assert dto.declining == 800
        assert dto.unchanged == 170
        assert dto.total_volume == 3000000000
        assert dto.market_cap == 750000000000000.0
        assert len(dto.top_gainers) == 1
        assert len(dto.top_losers) == 0
        assert len(dto.most_active) == 1


class TestSearchResultDTO:
    """Test cases for SearchResultDTO."""
    
    def test_search_result_dto_creation(self):
        """Test creating a SearchResultDTO instance."""
        # Arrange
        stocks = [
            StockDTO(
                id=i,
                ticker_symbol=f"{1000+i}",
                company_name=f"Company {i}",
                market="東証プライム",
                sector=None,
                industry=None,
                market_cap=None,
                description=None,
                created_at=None,
                updated_at=None,
            )
            for i in range(1, 4)
        ]
        
        # Act
        dto = SearchResultDTO(
            query="Company",
            total_results=3,
            results=stocks,
            suggestions=["Company A", "Company B", "Company C"]
        )
        
        # Assert
        assert dto.query == "Company"
        assert dto.total_results == 3
        assert len(dto.results) == 3
        assert dto.results[0].ticker_symbol == "1001"
        assert dto.suggestions == ["Company A", "Company B", "Company C"]
    
    def test_search_result_dto_empty_results(self):
        """Test SearchResultDTO with empty results."""
        # Act
        dto = SearchResultDTO(
            query="NonExistent",
            total_results=0,
            results=[],
            suggestions=[]
        )
        
        # Assert
        assert dto.query == "NonExistent"
        assert dto.total_results == 0
        assert dto.results == []
        assert dto.suggestions == []


class TestCreateStockDTO:
    """Test cases for CreateStockDTO."""
    
    def test_create_stock_dto_full(self):
        """Test creating a CreateStockDTO with all fields."""
        # Act
        dto = CreateStockDTO(
            ticker_symbol="9999",
            company_name="New Company Inc.",
            market="東証グロース",
            sector="情報・通信",
            industry="ソフトウェア",
            description="A new software company"
        )
        
        # Assert
        assert dto.ticker_symbol == "9999"
        assert dto.company_name == "New Company Inc."
        assert dto.market == "東証グロース"
        assert dto.sector == "情報・通信"
        assert dto.industry == "ソフトウェア"
        assert dto.description == "A new software company"
    
    def test_create_stock_dto_minimal(self):
        """Test creating a CreateStockDTO with minimal fields."""
        # Act
        dto = CreateStockDTO(
            ticker_symbol="8888",
            company_name="Minimal Inc.",
            market="東証スタンダード"
        )
        
        # Assert
        assert dto.ticker_symbol == "8888"
        assert dto.company_name == "Minimal Inc."
        assert dto.market == "東証スタンダード"
        assert dto.sector is None
        assert dto.industry is None
        assert dto.description is None


class TestUpdateStockDTO:
    """Test cases for UpdateStockDTO."""
    
    def test_update_stock_dto_full(self):
        """Test creating an UpdateStockDTO with all fields."""
        # Act
        dto = UpdateStockDTO(
            company_name="Updated Company Name",
            sector="エネルギー",
            industry="石油・ガス",
            description="Updated description",
            market_cap=50000000000.0
        )
        
        # Assert
        assert dto.company_name == "Updated Company Name"
        assert dto.sector == "エネルギー"
        assert dto.industry == "石油・ガス"
        assert dto.description == "Updated description"
        assert dto.market_cap == 50000000000.0
    
    def test_update_stock_dto_partial(self):
        """Test creating an UpdateStockDTO with partial fields."""
        # Act
        dto = UpdateStockDTO(
            sector="金融",
            market_cap=100000000000.0
        )
        
        # Assert
        assert dto.company_name is None
        assert dto.sector == "金融"
        assert dto.industry is None
        assert dto.description is None
        assert dto.market_cap == 100000000000.0
    
    def test_update_stock_dto_empty(self):
        """Test creating an UpdateStockDTO with no fields."""
        # Act
        dto = UpdateStockDTO()
        
        # Assert
        assert dto.company_name is None
        assert dto.sector is None
        assert dto.industry is None
        assert dto.description is None
        assert dto.market_cap is None