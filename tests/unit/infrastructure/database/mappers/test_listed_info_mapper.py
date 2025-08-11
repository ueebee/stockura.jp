"""Tests for ListedInfoMapper."""
import pytest
from datetime import date, datetime

from app.domain.entities.listed_info import ListedInfo
from app.domain.value_objects.stock_code import StockCode
from app.infrastructure.database.mappers.listed_info_mapper import ListedInfoMapper
from app.infrastructure.database.models.listed_info import ListedInfoModel


class TestListedInfoMapper:
    """Test cases for ListedInfoMapper."""
    
    @pytest.fixture
    def mapper(self):
        """Create mapper instance."""
        return ListedInfoMapper()
    
    @pytest.fixture
    def sample_entity(self):
        """Create sample ListedInfo entity."""
        return ListedInfo(
            date=date(2024, 1, 1),
            code=StockCode("1234"),
            company_name="Test Company",
            company_name_english="Test Company Inc.",
            sector_17_code="1",
            sector_17_code_name="Fishery",
            sector_33_code="0050",
            sector_33_code_name="Fishery",
            scale_category="1",
            market_code="0101",
            market_code_name="TSE1st",
            margin_code="1",
            margin_code_name="Margin Trading",
        )
    
    @pytest.fixture
    def sample_model(self):
        """Create sample ListedInfoModel."""
        return ListedInfoModel(
            date=date(2024, 1, 1),
            code="1234",
            company_name="Test Company",
            company_name_english="Test Company Inc.",
            sector_17_code="1",
            sector_17_code_name="Fishery",
            sector_33_code="0050",
            sector_33_code_name="Fishery",
            scale_category="1",
            market_code="0101",
            market_code_name="TSE1st",
            margin_code="1",
            margin_code_name="Margin Trading",
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=datetime(2024, 1, 1, 0, 0, 0),
        )
    
    def test_to_entity(self, mapper, sample_model):
        """Test converting model to entity."""
        entity = mapper.to_entity(sample_model)
        
        assert isinstance(entity, ListedInfo)
        assert entity.date == sample_model.date
        assert entity.code == StockCode(sample_model.code)
        assert entity.company_name == sample_model.company_name
        assert entity.company_name_english == sample_model.company_name_english
        assert entity.sector_17_code == sample_model.sector_17_code
        assert entity.sector_17_code_name == sample_model.sector_17_code_name
        assert entity.sector_33_code == sample_model.sector_33_code
        assert entity.sector_33_code_name == sample_model.sector_33_code_name
        assert entity.scale_category == sample_model.scale_category
        assert entity.market_code == sample_model.market_code
        assert entity.market_code_name == sample_model.market_code_name
        assert entity.margin_code == sample_model.margin_code
        assert entity.margin_code_name == sample_model.margin_code_name
    
    def test_to_model(self, mapper, sample_entity):
        """Test converting entity to model."""
        model = mapper.to_model(sample_entity)
        
        assert isinstance(model, ListedInfoModel)
        assert model.date == sample_entity.date
        assert model.code == sample_entity.code.value
        assert model.company_name == sample_entity.company_name
        assert model.company_name_english == sample_entity.company_name_english
        assert model.sector_17_code == sample_entity.sector_17_code
        assert model.sector_17_code_name == sample_entity.sector_17_code_name
        assert model.sector_33_code == sample_entity.sector_33_code
        assert model.sector_33_code_name == sample_entity.sector_33_code_name
        assert model.scale_category == sample_entity.scale_category
        assert model.market_code == sample_entity.market_code
        assert model.market_code_name == sample_entity.market_code_name
        assert model.margin_code == sample_entity.margin_code
        assert model.margin_code_name == sample_entity.margin_code_name
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)
    
    def test_to_entity_with_none_values(self, mapper):
        """Test converting model with None values to entity."""
        model = ListedInfoModel(
            date=date(2024, 1, 1),
            code="1234",
            company_name="Test Company",
            company_name_english=None,  # Optional field
            sector_17_code="1",
            sector_17_code_name="Fishery",
            sector_33_code="0050",
            sector_33_code_name="Fishery",
            scale_category="1",
            market_code="0101",
            market_code_name="TSE1st",
            margin_code=None,  # Optional field
            margin_code_name=None,  # Optional field
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=datetime(2024, 1, 1, 0, 0, 0),
        )
        
        entity = mapper.to_entity(model)
        
        assert entity.company_name_english is None
        assert entity.margin_code is None
        assert entity.margin_code_name is None
    
    def test_to_entities_batch(self, mapper, sample_model):
        """Test batch conversion from models to entities."""
        models = [sample_model, sample_model]
        entities = mapper.to_entities(models)
        
        assert len(entities) == 2
        assert all(isinstance(e, ListedInfo) for e in entities)
    
    def test_to_models_batch(self, mapper, sample_entity):
        """Test batch conversion from entities to models."""
        entities = [sample_entity, sample_entity]
        models = mapper.to_models(entities)
        
        assert len(models) == 2
        assert all(isinstance(m, ListedInfoModel) for m in models)