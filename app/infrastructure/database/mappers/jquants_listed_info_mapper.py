"""Mapper for JQuantsListedInfo entity and JQuantsListedInfoModel."""
from datetime import datetime, timezone
from typing import Optional

from app.domain.entities.jquants_listed_info import JQuantsListedInfo
from app.domain.value_objects.stock_code import StockCode
from app.infrastructure.database.mappers.base_mapper import BaseMapper
from app.infrastructure.database.models.jquants_listed_info import JQuantsListedInfoModel


class JQuantsListedInfoMapper(BaseMapper[JQuantsListedInfo, JQuantsListedInfoModel]):
    """Mapper for converting between JQuantsListedInfo entities and database models."""
    
    def to_entity(self, model: JQuantsListedInfoModel) -> JQuantsListedInfo:
        """Convert JQuantsListedInfoModel to JQuantsListedInfo entity.
        
        Args:
            model: Database model instance
            
        Returns:
            JQuantsListedInfo domain entity
        """
        return JQuantsListedInfo(
            date=model.date,
            code=StockCode(model.code),
            company_name=model.company_name,
            company_name_english=model.company_name_english,
            sector_17_code=model.sector_17_code,
            sector_17_code_name=model.sector_17_code_name,
            sector_33_code=model.sector_33_code,
            sector_33_code_name=model.sector_33_code_name,
            scale_category=model.scale_category,
            market_code=model.market_code,
            market_code_name=model.market_code_name,
            margin_code=model.margin_code,
            margin_code_name=model.margin_code_name,
        )
    
    def to_model(self, entity: JQuantsListedInfo) -> JQuantsListedInfoModel:
        """Convert JQuantsListedInfo entity to database model.
        
        Args:
            entity: Domain entity instance
            
        Returns:
            JQuantsListedInfoModel database model
        """
        return JQuantsListedInfoModel(
            date=entity.date,
            code=entity.code.value,
            company_name=entity.company_name,
            company_name_english=entity.company_name_english,
            sector_17_code=entity.sector_17_code,
            sector_17_code_name=entity.sector_17_code_name,
            sector_33_code=entity.sector_33_code,
            sector_33_code_name=entity.sector_33_code_name,
            scale_category=entity.scale_category,
            market_code=entity.market_code,
            market_code_name=entity.market_code_name,
            margin_code=entity.margin_code,
            margin_code_name=entity.margin_code_name,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )