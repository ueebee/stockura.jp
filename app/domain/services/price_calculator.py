"""Price calculation domain service."""
from decimal import Decimal
from typing import List, Optional

from app.domain.entities.price import Price
from app.domain.exceptions.stock_exceptions import InsufficientDataError


class PriceCalculator:
    """Domain service for price calculations."""

    @staticmethod
    def calculate_sma(prices: List[Price], period: int) -> Decimal:
        """Calculate Simple Moving Average (SMA).

        Args:
            prices: List of price entities
            period: Number of periods for SMA

        Returns:
            SMA value

        Raises:
            InsufficientDataError: If not enough data points
        """
        if len(prices) < period:
            raise InsufficientDataError(
                required=period,
                available=len(prices),
                operation="SMA calculation"
            )

        recent_prices = prices[-period:]
        total = sum(price.close for price in recent_prices)
        return total / period

    @staticmethod
    def calculate_ema(prices: List[Price], period: int) -> Decimal:
        """Calculate Exponential Moving Average (EMA).

        Args:
            prices: List of price entities
            period: Number of periods for EMA

        Returns:
            EMA value

        Raises:
            InsufficientDataError: If not enough data points
        """
        if len(prices) < period:
            raise InsufficientDataError(
                required=period,
                available=len(prices),
                operation="EMA calculation"
            )

        # Calculate initial SMA
        sma = PriceCalculator.calculate_sma(prices[:period], period)
        
        # Calculate EMA
        multiplier = Decimal(2) / (period + 1)
        ema = sma
        
        for price in prices[period:]:
            ema = (price.close - ema) * multiplier + ema
        
        return ema

    @staticmethod
    def calculate_rsi(prices: List[Price], period: int = 14) -> Decimal:
        """Calculate Relative Strength Index (RSI).

        Args:
            prices: List of price entities
            period: Number of periods for RSI (default: 14)

        Returns:
            RSI value (0-100)

        Raises:
            InsufficientDataError: If not enough data points
        """
        if len(prices) < period + 1:
            raise InsufficientDataError(
                required=period + 1,
                available=len(prices),
                operation="RSI calculation"
            )

        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i].close - prices[i-1].close
            if change > 0:
                gains.append(change)
                losses.append(Decimal(0))
            else:
                gains.append(Decimal(0))
                losses.append(abs(change))
        
        # Calculate average gain and loss
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return Decimal(100)
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    @staticmethod
    def calculate_volatility(prices: List[Price], period: int = 20) -> Decimal:
        """Calculate price volatility (standard deviation).

        Args:
            prices: List of price entities
            period: Number of periods for volatility

        Returns:
            Volatility value

        Raises:
            InsufficientDataError: If not enough data points
        """
        if len(prices) < period:
            raise InsufficientDataError(
                required=period,
                available=len(prices),
                operation="volatility calculation"
            )

        recent_prices = prices[-period:]
        returns = []
        
        for i in range(1, len(recent_prices)):
            daily_return = (
                (recent_prices[i].close - recent_prices[i-1].close) / 
                recent_prices[i-1].close
            )
            returns.append(daily_return)
        
        if not returns:
            return Decimal(0)
        
        # Calculate mean return
        mean_return = sum(returns) / len(returns)
        
        # Calculate variance
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        
        # Calculate standard deviation
        volatility = variance.sqrt() if hasattr(variance, 'sqrt') else Decimal(str(float(variance) ** 0.5))
        
        return volatility

    @staticmethod
    def calculate_vwap(prices: List[Price]) -> Optional[Decimal]:
        """Calculate Volume Weighted Average Price (VWAP).

        Args:
            prices: List of price entities

        Returns:
            VWAP value or None if no volume

        Raises:
            InsufficientDataError: If no data points
        """
        if not prices:
            raise InsufficientDataError(
                required=1,
                available=0,
                operation="VWAP calculation"
            )

        total_volume = sum(price.volume for price in prices)
        
        if total_volume == 0:
            return None
        
        typical_price_volume_sum = sum(
            ((price.high + price.low + price.close) / 3) * price.volume
            for price in prices
        )
        
        return typical_price_volume_sum / total_volume

    @staticmethod
    def identify_support_resistance(
        prices: List[Price],
        window: int = 5,
        threshold: Decimal = Decimal("0.02")
    ) -> dict[str, List[Decimal]]:
        """Identify support and resistance levels.

        Args:
            prices: List of price entities
            window: Window size for local min/max detection
            threshold: Threshold for grouping similar levels

        Returns:
            Dictionary with 'support' and 'resistance' levels
        """
        if len(prices) < window * 2:
            return {"support": [], "resistance": []}

        support_levels = []
        resistance_levels = []
        
        # Find local minima and maxima
        for i in range(window, len(prices) - window):
            # Check for local maximum (resistance)
            if all(prices[i].high >= prices[j].high for j in range(i - window, i + window + 1) if j != i):
                resistance_levels.append(prices[i].high)
            
            # Check for local minimum (support)
            if all(prices[i].low <= prices[j].low for j in range(i - window, i + window + 1) if j != i):
                support_levels.append(prices[i].low)
        
        # Group similar levels
        def group_levels(levels: List[Decimal]) -> List[Decimal]:
            if not levels:
                return []
            
            grouped = []
            levels_sorted = sorted(levels)
            current_group = [levels_sorted[0]]
            
            for level in levels_sorted[1:]:
                if abs(level - current_group[-1]) / current_group[-1] < threshold:
                    current_group.append(level)
                else:
                    grouped.append(sum(current_group) / len(current_group))
                    current_group = [level]
            
            if current_group:
                grouped.append(sum(current_group) / len(current_group))
            
            return grouped
        
        return {
            "support": group_levels(support_levels),
            "resistance": group_levels(resistance_levels)
        }