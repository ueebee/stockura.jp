from fastapi import APIRouter

from .endpoints import auth, schedules  # , listed_info_schedules

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(schedules.router)
# api_router.include_router(listed_info_schedules.router)
