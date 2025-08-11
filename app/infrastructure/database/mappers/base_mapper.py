"""Base mapper class for entity-model conversion."""
from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

TEntity = TypeVar('TEntity')
TModel = TypeVar('TModel')


class BaseMapper(ABC, Generic[TEntity, TModel]):
    """Abstract base mapper for converting between entities and database models.
    
    This class defines the interface for all mappers in the infrastructure layer,
    ensuring consistent conversion patterns across different entity types.
    """
    
    @abstractmethod
    def to_entity(self, model: TModel) -> TEntity:
        """Convert a database model to a domain entity.
        
        Args:
            model: The database model instance
            
        Returns:
            The corresponding domain entity
        """
        pass
    
    @abstractmethod
    def to_model(self, entity: TEntity) -> TModel:
        """Convert a domain entity to a database model.
        
        Args:
            entity: The domain entity instance
            
        Returns:
            The corresponding database model
        """
        pass
    
    def to_entities(self, models: List[TModel]) -> List[TEntity]:
        """Convert a list of database models to domain entities.
        
        Args:
            models: List of database model instances
            
        Returns:
            List of corresponding domain entities
        """
        return [self.to_entity(model) for model in models]
    
    def to_models(self, entities: List[TEntity]) -> List[TModel]:
        """Convert a list of domain entities to database models.
        
        Args:
            entities: List of domain entity instances
            
        Returns:
            List of corresponding database models
        """
        return [self.to_model(entity) for entity in entities]