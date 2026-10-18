"""FastAPI application factory."""
import json
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models.models import Problem
from app.api import health, auth, routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def auto_seed_database() -> None:
    """Ensure database schema is created and questions are seeded if empty."""
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            count = db.query(Problem).count()
            if count == 0:
                logger.info("Problem table is empty; seeding Striver SDE questions...")
                root_dir = Path(__file__).parent.parent.parent
                candidates = [
                    root_dir / "data" / "questions" / "striver_sde180_sample.json",
                    Path.cwd() / "data" / "questions" / "striver_sde180_sample.json",
                    Path.cwd().parent / "data" / "questions" / "striver_sde180_sample.json",
                ]
                questions_file = next((p for p in candidates if p.exists()), None)
                if questions_file:
                    with open(questions_file, encoding="utf-8") as f:
                        data = json.load(f)
                        questions = data.get("questions", data if isinstance(data, list) else [])
                    for q in questions:
                        prob_id = str(q.get("id") or q.get("problem_id", "")).strip()
                        if prob_id:
                            problem = Problem(
                                problem_id=prob_id,
                                sheet_order=int(q.get("sheet_order", 0)),
                                title=str(q.get("title", "")).strip(),
                                topic=str(q.get("topic", "")).strip(),
                                subtopic=str(q.get("subtopic") or "").strip() or None,
                                difficulty=str(q.get("difficulty") or "").strip() or None,
                                url=str(q.get("url") or "").strip() or None,
                                notes=str(q.get("notes") or "").strip() or None,
                            )
                            db.add(problem)
                    db.commit()
                    logger.info("Successfully seeded %d questions on startup.", len(questions))
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Auto-seed encountered an issue (non-fatal): %s", exc)


def create_app() -> FastAPI:
    app = FastAPI(
        title="DailyForge API",
        description="Striver SDE 180 DSA Tracker — personal productivity backend",
        version="1.0.0",
        docs_url="/docs" if settings.app_env == "development" else None,
        redoc_url="/redoc" if settings.app_env == "development" else None,
    )

    # Extract origin base from FRONTEND_URL (scheme + host without path)
    origin_base = None
    if settings.frontend_url:
        parsed = urlparse(settings.frontend_url)
        if parsed.scheme and parsed.netloc:
            origin_base = f"{parsed.scheme}://{parsed.netloc}"

    allowed_origins = [
        settings.frontend_url,
        origin_base,
        "https://geeky-rish.github.io",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    # Deduplicate and filter empty
    allowed_origins = list(dict.fromkeys(o for o in allowed_origins if o))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(routes.router)

    @app.on_event("startup")
    def startup():
        logger.info("DailyForge backend starting (env=%s)", settings.app_env)
        auto_seed_database()

    return app


app = create_app()
