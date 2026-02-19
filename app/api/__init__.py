from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.me import router as me_router
from app.api.routes.events import router as events_router
from app.api.routes.attendees import router as attendees_router
from app.api.routes.checkin import router as checkin_router
from app.api.routes.stats import router as stats_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(me_router)
api_router.include_router(events_router)
api_router.include_router(attendees_router)
api_router.include_router(checkin_router)
api_router.include_router(stats_router)