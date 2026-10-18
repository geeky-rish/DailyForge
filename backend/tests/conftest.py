"""Shared pytest fixtures for DailyForge backend tests."""
import os
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for tests
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_dailyforge.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("GITHUB_CLIENT_ID", "test-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("EMAIL_DRY_RUN", "true")
os.environ.setdefault("GITHUB_WRITE_TOKEN", "")
os.environ.setdefault("CHALLENGE_START_DATE", "2024-01-01")
os.environ.setdefault("AUTHORIZED_GITHUB_USERNAME", "geeky-rish")
os.environ.setdefault("AUTHORIZED_GITHUB_USER_ID", "12345678")

from app.core.database import Base, get_db
from app.main import app
from app.models.models import Problem, User, ChallengeState

TEST_DB_URL = "sqlite:///./test_dailyforge.db"


@pytest.fixture(scope="function")
def db():
    """Create a fresh test database for each test function."""
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        github_id=12345678,
        github_username="geeky-rish",
        github_avatar_url="https://avatars.githubusercontent.com/u/12345678",
        github_name="Rish",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_problems(db):
    """Create sample problems for testing."""
    problems = []
    for i in range(1, 11):
        p = Problem(
            problem_id=f"TEST{i:03d}",
            sheet_order=i,
            title=f"Test Problem {i}",
            topic="Arrays",
            subtopic="Test",
            difficulty="Medium",
            url=f"https://leetcode.com/problem-{i}/",
        )
        db.add(p)
        problems.append(p)
    db.commit()
    for p in problems:
        db.refresh(p)
    return problems


@pytest.fixture
def client(db):
    """FastAPI test client with overridden database."""
    from fastapi.testclient import TestClient

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
