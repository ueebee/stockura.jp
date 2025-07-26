"""Stock repository implementation."""
from typing import List, Optional

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories.stock_repository import (
    StockRepositoryInterface,
)
from app.core.logger import get_logger
from app.domain.entities.stock import Stock
from app.domain.value_objects.ticker_symbol import TickerSymbol
from app.infrastructure.database.models.stock_model import StockModel

logger = get_logger(__name__)


class StockRepositoryImpl(StockRepositoryInterface):
    """Stock repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository.

        Args:
            session: AsyncSession instance
        """
        self._session = session

    async def find_by_id(self, stock_id: int) -> Optional[Stock]:
        """Find stock by ID."""
        result = await self._session.execute(
            select(StockModel).where(StockModel.id == stock_id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            return self._to_entity(model)
        return None

    async def find_by_ticker(self, ticker_symbol: TickerSymbol) -> Optional[Stock]:
        """Find stock by ticker symbol."""
        result = await self._session.execute(
            select(StockModel).where(StockModel.ticker_symbol == ticker_symbol.value)
        )
        model = result.scalar_one_or_none()
        
        if model:
            return self._to_entity(model)
        return None

    async def find_all(
        self,
        market: Optional[str] = None,
        sector: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Stock]:
        """Find all stocks with optional filters."""
        query = select(StockModel)
        
        if market:
            query = query.where(StockModel.market == market)
        if sector:
            query = query.where(StockModel.sector == sector)
        
        query = query.limit(limit).offset(offset)
        
        result = await self._session.execute(query)
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]

    async def save(self, stock: Stock) -> Stock:
        """Save or update a stock."""
        model = self._to_model(stock)
        
        if stock.is_persisted:
            # Update existing
            await self._session.execute(
                update(StockModel)
                .where(StockModel.id == stock.id)
                .values(
                    company_name=model.company_name,
                    market=model.market,
                    sector=model.sector,
                    industry=model.industry,
                    market_cap=model.market_cap,
                    description=model.description,
                )
            )
            await self._session.flush()
            return stock
        else:
            # Create new
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            return self._to_entity(model)

    async def delete(self, stock_id: int) -> bool:
        """Delete a stock by ID."""
        result = await self._session.execute(
            select(StockModel).where(StockModel.id == stock_id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    async def exists(self, ticker_symbol: TickerSymbol) -> bool:
        """Check if stock exists by ticker symbol."""
        result = await self._session.execute(
            select(func.count(StockModel.id))
            .where(StockModel.ticker_symbol == ticker_symbol.value)
        )
        count = result.scalar()
        return count > 0

    async def count(
        self,
        market: Optional[str] = None,
        sector: Optional[str] = None
    ) -> int:
        """Count stocks with optional filters."""
        query = select(func.count(StockModel.id))
        
        if market:
            query = query.where(StockModel.market == market)
        if sector:
            query = query.where(StockModel.sector == sector)
        
        result = await self._session.execute(query)
        return result.scalar() or 0

    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Stock]:
        """Search stocks by company name or ticker."""
        search_pattern = f"%{query}%"
        
        result = await self._session.execute(
            select(StockModel)
            .where(
                or_(
                    StockModel.ticker_symbol.ilike(search_pattern),
                    StockModel.company_name.ilike(search_pattern)
                )
            )
            .limit(limit)
        )
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]

    async def find_by_market(self, market: str) -> List[Stock]:
        """Find all stocks in a specific market."""
        result = await self._session.execute(
            select(StockModel).where(StockModel.market == market)
        )
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]

    async def update_market_cap(
        self,
        ticker_symbol: TickerSymbol,
        market_cap: float
    ) -> bool:
        """Update market capitalization for a stock."""
        result = await self._session.execute(
            update(StockModel)
            .where(StockModel.ticker_symbol == ticker_symbol.value)
            .values(market_cap=market_cap)
            .returning(StockModel.id)
        )
        updated_id = result.scalar_one_or_none()
        await self._session.flush()
        
        return updated_id is not None

    def _to_entity(self, model: StockModel) -> Stock:
        """Convert model to entity.

        Args:
            model: Stock model

        Returns:
            Stock entity
        """
        return Stock(
            id=model.id,
            ticker_symbol=TickerSymbol(model.ticker_symbol),
            company_name=model.company_name,
            market=model.market,
            sector=model.sector,
            industry=model.industry,
            market_cap=model.market_cap,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Stock) -> StockModel:
        """Convert entity to model.

        Args:
            entity: Stock entity

        Returns:
            Stock model
        """
        return StockModel(
            id=entity.id,
            ticker_symbol=entity.ticker_symbol.value,
            company_name=entity.company_name,
            market=entity.market,
            sector=entity.sector,
            industry=entity.industry,
            market_cap=entity.market_cap,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )