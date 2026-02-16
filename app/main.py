from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import api_router
from app.core.config import settings
from app.db.session import engine


def create_app() -> FastAPI:
    app = FastAPI(title="QR Check-in API", version="0.1.0")

    # CORS (production: set strict origins)
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.ENV}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ready"}
        except Exception:
            return {"status": "not_ready"}

    app.include_router(api_router)
    return app


app = create_app()
