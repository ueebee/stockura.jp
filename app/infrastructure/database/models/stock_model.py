"""Stock database model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint

from app.infrastructure.database.connection import Base


class StockModel(Base):
    """Stock SQLAlchemy model."""

    __tablename__ = "stocks"
    __table_args__ = (
        UniqueConstraint("ticker_symbol", name="uq_stocks_ticker_symbol"),
    )

    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String(10), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    market = Column(String(50), nullable=False, index=True)
    sector = Column(String(100), nullable=True, index=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Float, nullable=True)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<StockModel(ticker_symbol='{self.ticker_symbol}', company_name='{self.company_name}')>"


class PriceModel(Base):
    """Price SQLAlchemy model."""

    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("ticker_symbol", "timestamp", name="uq_prices_ticker_timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    adjusted_close = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<PriceModel(ticker_symbol='{self.ticker_symbol}', timestamp='{self.timestamp}', close={self.close})>"