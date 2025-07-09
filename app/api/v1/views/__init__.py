# HTMXビューエンドポイント
from .dashboard import router as dashboard_router
from .data_sources import router as data_sources_router
from .jobs import router as jobs_router
from .analysis import router as analysis_router
from .settings import router as settings_router

__all__ = [
    "dashboard_router",
    "data_sources_router", 
    "jobs_router",
    "analysis_router",
    "settings_router"
]