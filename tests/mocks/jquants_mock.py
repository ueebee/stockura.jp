"""Mock classes for JQuants API testing."""
from datetime import date, datetime
from typing import List, Optional

from app.domain.entities.price import Price
from app.domain.entities.stock import Stock
from app.domain.exceptions.jquants_exceptions import JQuantsException
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.domain.value_objects.time_period import TimePeriod


class MockJQuantsClient:
    """Mock JQuants client for testing."""

    def __init__(self, scenario: str = "success"):
        """Initialize mock client.
        
        Args:
            scenario: Test scenario ('success', 'error', 'not_found', 'insufficient_data')
        """
        self.scenario = scenario
        self.call_count = 0
        
    async def get_stock_info(self, ticker_symbol: TickerSymbol) -> Optional[Stock]:
        """Mock get stock info."""
        self.call_count += 1
        
        if self.scenario == "error":
            raise JQuantsException("Mock API error")
        elif self.scenario == "not_found":
            return None
        else:
            from app.domain.entities.stock import StockCode, MarketCode, SectorCode17, SectorCode33
            
            return Stock(
                code=StockCode(ticker_symbol.value),
                company_name=f"Mock Company {ticker_symbol.value}",
                company_name_english=f"Mock Company {ticker_symbol.value} Ltd.",
                sector_17_code=SectorCode17.FOODS,
                sector_17_name="食品",
                sector_33_code=SectorCode33.FISHERY_AGRICULTURE_FORESTRY,
                sector_33_name="水産・農林業",
                scale_category="1",
                market_code=MarketCode.PRIME,
                market_name="プライム市場"
            )
    
    async def get_stock_prices(
        self, 
        ticker_symbol: TickerSymbol, 
        period: TimePeriod
    ) -> List[Price]:
        """Mock get stock prices."""
        self.call_count += 1
        
        if self.scenario == "error":
            raise JQuantsException("Mock API error")
        elif self.scenario == "insufficient_data":
            # Return only 10 prices (less than required 20)
            return self._generate_mock_prices(ticker_symbol, 10)
        elif self.scenario == "not_found":
            return []
        else:
            # Return 100 prices for success scenario
            return self._generate_mock_prices(ticker_symbol, 100)
    
    def _generate_mock_prices(self, ticker_symbol: TickerSymbol, count: int) -> List[Price]:
        """Generate mock price data."""
        from datetime import timedelta
        
        prices = []
        base_price = 1000.0
        start_date = date(2024, 1, 1)
        
        for i in range(count):
            # Create some price movement
            price_change = (i % 10 - 5) * 10  # -50 to +50
            close_price = base_price + price_change
            
            price = Price(
                ticker_symbol=ticker_symbol,
                date=start_date + timedelta(days=i),
                open=close_price - 10,
                high=close_price + 20,
                low=close_price - 20,
                close=close_price,
                volume=1000000 + i * 10000
            )
            prices.append(price)
            
        return prices


class MockYFinanceClient:
    """Mock YFinance client for testing."""
    
    def __init__(self, scenario: str = "success"):
        """Initialize mock client."""
        self.scenario = scenario
        self.call_count = 0
        
    async def get_stock_info(self, ticker_symbol: TickerSymbol) -> Optional[Stock]:
        """Mock get stock info."""
        self.call_count += 1
        
        if self.scenario == "error":
            raise Exception("Mock YFinance error")
        elif self.scenario == "not_found":
            return None
        else:
            from app.domain.entities.stock import StockCode, MarketCode, SectorCode17, SectorCode33
            
            return Stock(
                code=StockCode(ticker_symbol.value),
                company_name=f"YFinance Company {ticker_symbol.value}",
                company_name_english=f"YFinance Company {ticker_symbol.value} Ltd.",
                sector_17_code=SectorCode17.FOODS,
                sector_17_name="食品",
                sector_33_code=SectorCode33.FISHERY_AGRICULTURE_FORESTRY,
                sector_33_name="水産・農林業",
                scale_category="1",
                market_code=MarketCode.PRIME,
                market_name="プライム市場"
            )
    
    async def get_stock_prices(
        self, 
        ticker_symbol: TickerSymbol, 
        period: TimePeriod,
        interval: str = "1d"
    ) -> List[Price]:
        """Mock get stock prices."""
        self.call_count += 1
        
        if self.scenario == "error":
            raise Exception("Mock YFinance error")
        else:
            # Return similar data as JQuants mock
            return MockJQuantsClient(self.scenario)._generate_mock_prices(ticker_symbol, 100)