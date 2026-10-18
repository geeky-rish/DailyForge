"""Question scheduling service — the core business logic for DailyForge.

Rules:
- Assign exactly QUESTIONS_PER_DAY (default 2) eligible, unsolved questions per local calendar day.
- Respect original sheet order.
- Never assign a question already marked solved.
- Preserve assigned questions for the day across backend restarts.
- Track extra questions independently of daily assignment.
- Solving 3+ questions on one day must not reduce tomorrow's target.
- Marking attempted must not mark solved.
- Support deferred questions.
- Prevent duplicate daily assignments when a scheduled job retries.
- When all questions complete, show completion state.
- Use Asia/Kolkata for day boundaries.
"""
import logging
from datetime import date, datetime, timezone
from typing import Optional

import pytz
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import (
    DailyAssignment, DailyAssignmentProblem, Problem, ProblemProgress, User
)

logger = logging.getLogger(__name__)
IST = pytz.timezone(settings.timezone)


def get_today_ist() -> str:
    """Return today's date string YYYY-MM-DD in Asia/Kolkata."""
    return datetime.now(IST).strftime("%Y-%m-%d")


def get_challenge_day(start_date_str: str, reference_date_str: Optional[str] = None) -> int:
    """Return 1-based challenge day number. Day 1 = start_date."""
    start = date.fromisoformat(start_date_str)
    ref = date.fromisoformat(reference_date_str) if reference_date_str else date.fromisoformat(get_today_ist())
    delta = (ref - start).days
    return max(1, delta + 1)


def get_or_create_daily_assignment(db: Session, user: User) -> DailyAssignment:
    """
    Idempotent: return today's assignment if it exists, otherwise create it.
    Never creates duplicate assignments for the same (user, date).
    """
    today = get_today_ist()
    existing = db.execute(
        select(DailyAssignment).where(
            and_(DailyAssignment.user_id == user.id, DailyAssignment.assignment_date == today)
        )
    ).scalar_one_or_none()

    if existing:
        logger.debug("Daily assignment for %s on %s already exists (id=%d)", user.github_username, today, existing.id)
        return existing

    # Determine challenge day
    challenge_day = get_challenge_day(settings.challenge_start_date, today)

    # Find solved problem IDs to exclude
    solved_progress = db.execute(
        select(ProblemProgress.problem_id).where(
            and_(ProblemProgress.user_id == user.id, ProblemProgress.status == "solved")
        )
    ).scalars().all()
    solved_ids = set(solved_progress)

    # Find already-assigned problem IDs (from any previous day) to avoid re-assigning
    assigned_problem_ids = db.execute(
        select(DailyAssignmentProblem.problem_id)
        .join(DailyAssignment, DailyAssignmentProblem.assignment_id == DailyAssignment.id)
        .where(DailyAssignment.user_id == user.id)
    ).scalars().all()
    assigned_ids = set(assigned_problem_ids)

    # Exclude both solved and already assigned
    exclude_ids = solved_ids | assigned_ids

    # Get eligible problems in sheet order
    eligible = db.execute(
        select(Problem).where(
            and_(Problem.is_active == True, Problem.id.notin_(exclude_ids))  # noqa: E712
        ).order_by(Problem.sheet_order)
        .limit(settings.questions_per_day)
    ).scalars().all()

    # Create assignment record
    assignment = DailyAssignment(
        user_id=user.id,
        assignment_date=today,
        challenge_day=challenge_day,
    )
    db.add(assignment)
    db.flush()  # get assignment.id

    for pos, problem in enumerate(eligible):
        db.add(DailyAssignmentProblem(
            assignment_id=assignment.id,
            problem_id=problem.id,
            position=pos,
        ))

    db.commit()
    db.refresh(assignment)
    logger.info(
        "Created daily assignment for %s on %s: day %d, %d problems",
        user.github_username, today, challenge_day, len(eligible)
    )
    return assignment


def mark_problem_attempted(db: Session, user: User, problem_db_id: int) -> ProblemProgress:
    """Mark a problem as attempted — does NOT mark it solved."""
    progress = _get_or_create_progress(db, user, problem_db_id)
    if progress.status not in ("solved",):
        progress.status = "attempted"
    progress.attempts += 1
    progress.last_attempted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(progress)
    return progress


def mark_problem_solved(db: Session, user: User, problem_db_id: int, is_extra: bool = False) -> ProblemProgress:
    """Mark a problem as solved. is_extra=True for questions solved beyond the daily 2."""
    progress = _get_or_create_progress(db, user, problem_db_id)
    progress.status = "solved"
    progress.attempts = max(progress.attempts, 1)
    if not progress.solved_at:
        progress.solved_at = datetime.now(timezone.utc)
    progress.is_extra = is_extra
    db.commit()
    db.refresh(progress)
    return progress


def mark_problem_deferred(db: Session, user: User, problem_db_id: int) -> ProblemProgress:
    """Defer a problem."""
    progress = _get_or_create_progress(db, user, problem_db_id)
    if progress.status != "solved":
        progress.status = "deferred"
    db.commit()
    db.refresh(progress)
    return progress


def mark_problem_needs_revision(db: Session, user: User, problem_db_id: int) -> ProblemProgress:
    """Mark a solved problem as needing revision."""
    progress = _get_or_create_progress(db, user, problem_db_id)
    progress.status = "needs_revision"
    db.commit()
    db.refresh(progress)
    return progress


def get_progress_stats(db: Session, user: User) -> dict:
    """Return aggregate progress statistics for the user."""
    all_progress = db.execute(
        select(ProblemProgress).where(ProblemProgress.user_id == user.id)
    ).scalars().all()

    total_problems = db.execute(select(Problem).where(Problem.is_active == True)).scalars().all()  # noqa: E712
    total = len(total_problems)
    solved = sum(1 for p in all_progress if p.status == "solved")
    attempted = sum(1 for p in all_progress if p.status == "attempted")
    deferred = sum(1 for p in all_progress if p.status == "deferred")
    needs_revision = sum(1 for p in all_progress if p.status == "needs_revision")
    extra = sum(1 for p in all_progress if p.is_extra)

    return {
        "total": total,
        "solved": solved,
        "attempted_not_solved": attempted,
        "deferred": deferred,
        "needs_revision": needs_revision,
        "remaining": max(0, total - solved),
        "extra_questions_solved": extra,
        "completion_pct": round(solved / total * 100, 1) if total else 0,
        "is_complete": total > 0 and solved >= total,
    }


def _get_or_create_progress(db: Session, user: User, problem_db_id: int) -> ProblemProgress:
    progress = db.execute(
        select(ProblemProgress).where(
            and_(ProblemProgress.user_id == user.id, ProblemProgress.problem_id == problem_db_id)
        )
    ).scalar_one_or_none()
    if not progress:
        progress = ProblemProgress(user_id=user.id, problem_id=problem_db_id)
        db.add(progress)
        db.flush()
    return progress
