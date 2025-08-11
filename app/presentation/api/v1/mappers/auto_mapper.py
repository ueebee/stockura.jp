"""Automatic field mapping utility."""

import dataclasses
from typing import Any, Dict, Type, TypeVar, get_args, get_origin
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel

T = TypeVar("T")


class AutoMapper:
    """Automatic field mapping utility for converting between Pydantic models and dataclasses."""

    @staticmethod
    def map_fields(source: Any, target_class: Type[T]) -> Dict[str, Any]:
        """Map fields from source to target class automatically.
        
        This method automatically maps fields with the same name and compatible types
        from the source object to a dictionary that can be used to instantiate the
        target class.
        
        Args:
            source: The source object (can be Pydantic model, dataclass, or dict)
            target_class: The target class to map to
            
        Returns:
            A dictionary of mapped fields
        """
        # Get source data as dictionary
        if isinstance(source, BaseModel):
            source_data = source.model_dump()
        elif dataclasses.is_dataclass(source):
            source_data = dataclasses.asdict(source)
        elif isinstance(source, dict):
            source_data = source
        else:
            # For other objects, try to get their __dict__
            source_data = source.__dict__ if hasattr(source, "__dict__") else {}
        
        # Get target field information
        target_fields = AutoMapper._get_target_fields(target_class)
        
        # Map fields
        mapped_fields = {}
        for field_name, field_info in target_fields.items():
            if field_name in source_data:
                value = source_data[field_name]
                # Skip None values unless the field is explicitly Optional
                if value is not None:
                    mapped_fields[field_name] = AutoMapper._convert_value(
                        value, field_info["type"]
                    )
                elif field_info.get("has_default", False) or field_info.get("is_optional", False):
                    # Include None for optional fields or fields with defaults
                    mapped_fields[field_name] = None
        
        return mapped_fields

    @staticmethod
    def _get_target_fields(target_class: Type[T]) -> Dict[str, Dict[str, Any]]:
        """Get field information from the target class.
        
        Args:
            target_class: The target class
            
        Returns:
            Dictionary of field names to field information
        """
        fields = {}
        
        if dataclasses.is_dataclass(target_class):
            # Handle dataclass
            for field in dataclasses.fields(target_class):
                field_type = field.type
                has_default = field.default != dataclasses.MISSING or field.default_factory != dataclasses.MISSING
                is_optional = AutoMapper._is_optional_type(field_type)
                fields[field.name] = {
                    "type": field_type,
                    "has_default": has_default,
                    "is_optional": is_optional
                }
        elif issubclass(target_class, BaseModel):
            # Handle Pydantic model
            for field_name, field_info in target_class.model_fields.items():
                field_type = field_info.annotation
                has_default = field_info.default is not None or field_info.default_factory is not None
                is_optional = not field_info.is_required() or AutoMapper._is_optional_type(field_type)
                fields[field_name] = {
                    "type": field_type,
                    "has_default": has_default,
                    "is_optional": is_optional
                }
        
        return fields

    @staticmethod
    def _is_optional_type(field_type: Any) -> bool:
        """Check if a type is Optional (Union with None).
        
        Args:
            field_type: The field type to check
            
        Returns:
            True if the type is Optional
        """
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            return type(None) in args
        return False

    @staticmethod
    def _convert_value(value: Any, target_type: Type) -> Any:
        """Convert a value to the target type if necessary.
        
        Args:
            value: The value to convert
            target_type: The target type
            
        Returns:
            The converted value
        """
        # Handle None
        if value is None:
            return None
        
        # Get the actual type if it's Optional
        actual_type = target_type
        origin = get_origin(target_type)
        if origin is Union:
            args = get_args(target_type)
            # Get the non-None type from Optional
            actual_type = next((arg for arg in args if arg is not type(None)), target_type)
        
        # Get origin of actual_type for checking generic types
        actual_origin = get_origin(actual_type)
        
        # Handle common type conversions
        if actual_type in (str, int, float, bool):
            return actual_type(value)
        elif actual_type in (datetime, date):
            if isinstance(value, str):
                return datetime.fromisoformat(value) if actual_type == datetime else date.fromisoformat(value)
            return value
        elif actual_type == UUID:
            if isinstance(value, str):
                return UUID(value)
            return value
        
        # Handle nested conversions for lists
        if actual_origin is list:
            item_type = get_args(actual_type)[0] if get_args(actual_type) else Any
            if isinstance(value, list):
                return [AutoMapper._convert_value(item, item_type) for item in value]
        
        # Check if value is already the correct type (for non-generic types)
        if actual_origin is None:
            try:
                if isinstance(value, actual_type):
                    return value
            except TypeError:
                # Handle case where isinstance fails with generic types
                pass
        
        # For complex types, return as-is and let the caller handle it
        return value


# Import Union for Optional type handling
from typing import Union