"""Factory for creating test price data."""
import factory
import factory.fuzzy
from datetime import date, timedelta
from app.domain.entities.price import Price
from app.domain.value_objects.ticker_symbol import TickerSymbol


class PriceFactory(factory.Factory):
    """Factory for creating Price entities."""
    
    class Meta:
        model = Price
    
    ticker_symbol = factory.LazyFunction(lambda: TickerSymbol("1234"))
    date = factory.Sequence(lambda n: date(2024, 1, 1) + timedelta(days=n))
    open = factory.fuzzy.FuzzyFloat(900.0, 1100.0)
    high = factory.LazyAttribute(lambda obj: obj.open + factory.fuzzy.FuzzyFloat(0, 50).fuzz())
    low = factory.LazyAttribute(lambda obj: obj.open - factory.fuzzy.FuzzyFloat(0, 50).fuzz())
    close = factory.fuzzy.FuzzyFloat(900.0, 1100.0)
    volume = factory.fuzzy.FuzzyInteger(100000, 10000000)
    
    @classmethod
    def create_batch_with_trend(cls, size: int, ticker_symbol: str, base_price: float = 1000.0, trend: str = "neutral"):
        """Create a batch of prices with a specific trend.
        
        Args:
            size: Number of prices to create
            ticker_symbol: Ticker symbol for all prices
            base_price: Starting price
            trend: 'bullish', 'bearish', or 'neutral'
        """
        prices = []
        ticker = TickerSymbol(ticker_symbol)
        
        for i in range(size):
            if trend == "bullish":
                # Upward trend with some volatility
                price_change = i * 2 + factory.fuzzy.FuzzyFloat(-5, 10).fuzz()
            elif trend == "bearish":
                # Downward trend with some volatility
                price_change = -i * 2 + factory.fuzzy.FuzzyFloat(-10, 5).fuzz()
            else:
                # Neutral/sideways movement
                price_change = factory.fuzzy.FuzzyFloat(-10, 10).fuzz()
            
            close_price = base_price + price_change
            open_price = close_price + factory.fuzzy.FuzzyFloat(-10, 10).fuzz()
            
            price = Price(
                ticker_symbol=ticker,
                date=date(2024, 1, 1) + timedelta(days=i),
                open=open_price,
                high=max(open_price, close_price) + factory.fuzzy.FuzzyFloat(0, 20).fuzz(),
                low=min(open_price, close_price) - factory.fuzzy.FuzzyFloat(0, 20).fuzz(),
                close=close_price,
                volume=factory.fuzzy.FuzzyInteger(100000, 1000000).fuzz()
            )
            prices.append(price)
            
        return prices
    
    @classmethod
    def create_volatile_batch(cls, size: int, ticker_symbol: str):
        """Create prices with high volatility."""
        prices = []
        ticker = TickerSymbol(ticker_symbol)
        base_price = 1000.0
        
        for i in range(size):
            # High volatility pattern
            volatility = factory.fuzzy.FuzzyFloat(-100, 100).fuzz()
            close_price = base_price + volatility
            
            price = Price(
                ticker_symbol=ticker,
                date=date(2024, 1, 1) + timedelta(days=i),
                open=base_price,
                high=close_price + abs(volatility),
                low=close_price - abs(volatility),
                close=close_price,
                volume=factory.fuzzy.FuzzyInteger(100000, 1000000).fuzz()
            )
            prices.append(price)
            base_price = close_price  # Next day starts from previous close
            
        return prices
    
    @classmethod
    def create_zero_volume_batch(cls, size: int, ticker_symbol: str):
        """Create prices with zero volume."""
        prices = cls.create_batch(size)
        for price in prices:
            price.volume = 0
        return prices