from fastapi import APIRouter

from .endpoints import announcement, auth, schedules, trades_spec, weekly_margin_interest

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(schedules.router)
api_router.include_router(trades_spec.router, prefix="/trades-spec", tags=["trades-spec"])
api_router.include_router(weekly_margin_interest.router, prefix="/weekly-margin-interest", tags=["weekly-margin-interest"])
api_router.include_router(announcement.router, prefix="/announcement", tags=["announcement"])
