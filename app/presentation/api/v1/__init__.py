from fastapi import APIRouter

from .endpoints import auth, schedules, trades_spec

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(schedules.router)
api_router.include_router(trades_spec.router, prefix="/trades-spec", tags=["trades-spec"])
