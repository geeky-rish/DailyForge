"""Streak calculation service.

Rules:
- Streak is based on actual recorded study sessions, not uptime or button clicks.
- A streak must not be incremented twice on the same date.
- A missed day breaks the streak (resets to 0 for the next session).
- Streak calculation uses Asia/Kolkata dates.
"""
import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import ChallengeState, StudySession, User
from app.services.scheduler import get_today_ist

logger = logging.getLogger(__name__)


def record_study_session(
    db: Session,
    user: User,
    questions_solved: int,
    duration_minutes: Optional[int] = None,
    notes: Optional[str] = None,
) -> StudySession:
    """
    Record a genuine study session. Idempotent: only one session per calendar day.
    Updates streak and challenge state.
    """
    from datetime import timezone
    from datetime import datetime

    today = get_today_ist()

    # Idempotency: return existing session if already recorded today
    existing = db.execute(
        select(StudySession).where(
            StudySession.user_id == user.id,
            StudySession.session_date == today,
        )
    ).scalar_one_or_none()

    if existing:
        logger.info("Study session for %s on %s already recorded (id=%d)", user.github_username, today, existing.id)
        return existing

    from app.services.scheduler import get_challenge_day
    from app.core.config import settings
    challenge_day = get_challenge_day(settings.challenge_start_date, today)

    session = StudySession(
        user_id=user.id,
        session_date=today,
        challenge_day=challenge_day,
        questions_solved=questions_solved,
        duration_minutes=duration_minutes,
        notes=notes,
        created_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.flush()

    # Update streak
    _update_streak(db, user, today)

    db.commit()
    db.refresh(session)
    logger.info("Recorded study session for %s on %s (day %d)", user.github_username, today, challenge_day)
    return session


def _update_streak(db: Session, user: User, today_str: str) -> None:
    """Recalculate streak for the user based on session history."""
    today = date.fromisoformat(today_str)

    state = db.execute(
        select(ChallengeState).where(ChallengeState.user_id == user.id)
    ).scalar_one_or_none()

    if not state:
        from app.core.config import settings
        state = ChallengeState(user_id=user.id, start_date=settings.challenge_start_date)
        db.add(state)
        db.flush()

    last_date = date.fromisoformat(state.last_session_date) if state.last_session_date else None

    if last_date is None:
        # First session ever
        state.current_streak = 1
    elif last_date == today:
        # Same day, don't increment
        pass
    elif last_date == today - timedelta(days=1):
        # Consecutive day
        state.current_streak += 1
    else:
        # Gap — reset streak
        state.current_streak = 1

    state.last_session_date = today_str
    state.longest_streak = max(state.longest_streak, state.current_streak)

    from datetime import datetime, timezone
    state.updated_at = datetime.now(timezone.utc)


def get_streak_info(db: Session, user: User) -> dict:
    """Return current streak, longest streak, and recent session history."""
    state = db.execute(
        select(ChallengeState).where(ChallengeState.user_id == user.id)
    ).scalar_one_or_none()

    sessions = db.execute(
        select(StudySession)
        .where(StudySession.user_id == user.id)
        .order_by(StudySession.session_date.desc())
        .limit(14)
    ).scalars().all()

    return {
        "current_streak": state.current_streak if state else 0,
        "longest_streak": state.longest_streak if state else 0,
        "last_session_date": state.last_session_date if state else None,
        "recent_sessions": [
            {
                "date": s.session_date,
                "challenge_day": s.challenge_day,
                "questions_solved": s.questions_solved,
                "github_updated": s.github_updated,
            }
            for s in sessions
        ],
    }
