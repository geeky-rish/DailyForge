"""FastAPI application factory."""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api import health, auth, routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="DailyForge API",
        description="Striver SDE 180 DSA Tracker — personal productivity backend",
        version="1.0.0",
        docs_url="/docs" if settings.app_env == "development" else None,
        redoc_url="/redoc" if settings.app_env == "development" else None,
    )

    # CORS — only allow configured origins
    allowed_origins = [
        settings.frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    # Deduplicate
    allowed_origins = list(dict.fromkeys(o for o in allowed_origins if o))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(routes.router)

    @app.on_event("startup")
    def startup():
        logger.info("DailyForge backend starting (env=%s)", settings.app_env)

    return app


app = create_app()
