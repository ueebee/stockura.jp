"""Base mapper for converting between API schemas and DTOs."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TSchema = TypeVar("TSchema")
TDto = TypeVar("TDto")


class BaseMapper(ABC, Generic[TSchema, TDto]):
    """Base mapper for converting between API schemas and DTOs."""

    @abstractmethod
    def schema_to_dto(self, schema: TSchema) -> TDto:
        """Convert API schema to DTO.
        
        Args:
            schema: The API schema to convert
            
        Returns:
            The corresponding DTO
        """
        pass

    @abstractmethod
    def dto_to_schema(self, dto: TDto) -> TSchema:
        """Convert DTO to API schema.
        
        Args:
            dto: The DTO to convert
            
        Returns:
            The corresponding API schema
        """
        pass