"""Dependency injection for mappers."""

from app.presentation.api.v1.mappers.schedule_mapper import (
    ScheduleCreateMapper,
    ScheduleListResponseMapper,
    ScheduleResponseMapper,
    ScheduleUpdateMapper,
)


def get_schedule_create_mapper() -> ScheduleCreateMapper:
    """Get ScheduleCreateMapper instance."""
    return ScheduleCreateMapper()


def get_schedule_update_mapper() -> ScheduleUpdateMapper:
    """Get ScheduleUpdateMapper instance."""
    return ScheduleUpdateMapper()


def get_schedule_response_mapper() -> ScheduleResponseMapper:
    """Get ScheduleResponseMapper instance."""
    return ScheduleResponseMapper()


def get_schedule_list_response_mapper() -> ScheduleListResponseMapper:
    """Get ScheduleListResponseMapper instance."""
    return ScheduleListResponseMapper()