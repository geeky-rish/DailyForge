"""Main API router — dashboard, progress, study sessions, GitHub README."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import DailyAssignment, DailyAssignmentProblem, Problem, StudySession, User
from app.services import scheduler, streak as streak_svc, quotes as quote_svc, github_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class ProblemStatusUpdate(BaseModel):
    problem_db_id: int
    is_extra: bool = False


class StudySessionCreate(BaseModel):
    questions_solved: int
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None


class GitHubUpdateRequest(BaseModel):
    session_id: int
    dry_run: bool = False


# ─── Helpers ────────────────────────────────────────────────────────────────

def _serialize_problem(p: Problem, status_map: dict) -> dict:
    prog = status_map.get(p.id)
    return {
        "id": p.id,
        "problem_id": p.problem_id,
        "sheet_order": p.sheet_order,
        "title": p.title,
        "topic": p.topic,
        "subtopic": p.subtopic,
        "difficulty": p.difficulty,
        "url": p.url,
        "notes": p.notes,
        "status": prog.status if prog else "unsolved",
        "attempts": prog.attempts if prog else 0,
        "solved_at": prog.solved_at.isoformat() if prog and prog.solved_at else None,
        "is_extra": prog.is_extra if prog else False,
    }


# ─── Me ─────────────────────────────────────────────────────────────────────

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "github_id": current_user.github_id,
        "username": current_user.github_username,
        "name": current_user.github_name,
        "avatar_url": current_user.github_avatar_url,
    }


# ─── Dashboard ──────────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return complete dashboard data for the authenticated user."""
    today = scheduler.get_today_ist()
    challenge_day = scheduler.get_challenge_day(settings.challenge_start_date, today)

    # Get or create today's assignment
    assignment = scheduler.get_or_create_daily_assignment(db, current_user)

    # Serialize assignment problems
    from app.models.models import ProblemProgress
    progress_map = {
        p.problem_id: p
        for p in db.execute(
            select(ProblemProgress).where(ProblemProgress.user_id == current_user.id)
        ).scalars().all()
    }

    assigned_problems = []
    for ap in sorted(assignment.problems, key=lambda x: x.position):
        assigned_problems.append(_serialize_problem(ap.problem, progress_map))

    # Stats
    stats = scheduler.get_progress_stats(db, current_user)

    # Streak
    streak_info = streak_svc.get_streak_info(db, current_user)

    # Quote
    quote = quote_svc.get_quote_for_day(db, challenge_day)

    # Assignment completion
    solved_today = sum(
        1 for ap in assignment.problems
        if progress_map.get(ap.problem_id) and progress_map[ap.problem_id].status == "solved"
    )
    assignment_complete = solved_today >= len(assignment.problems) and len(assignment.problems) > 0

    return {
        "today": today,
        "challenge_day": challenge_day,
        "assignment": {
            "id": assignment.id,
            "date": assignment.assignment_date,
            "is_complete": assignment_complete,
            "problems": assigned_problems,
            "total_assigned": len(assigned_problems),
            "solved_count": solved_today,
        },
        "stats": stats,
        "streak": streak_info,
        "quote": quote,
    }


# ─── Problem status updates ──────────────────────────────────────────────────

@router.post("/problems/{problem_db_id}/attempted")
def mark_attempted(
    problem_db_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    problem = db.get(Problem, problem_db_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    progress = scheduler.mark_problem_attempted(db, current_user, problem_db_id)
    return {"status": progress.status, "attempts": progress.attempts}


@router.post("/problems/{problem_db_id}/solved")
def mark_solved(
    problem_db_id: int,
    body: ProblemStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    problem = db.get(Problem, problem_db_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    progress = scheduler.mark_problem_solved(db, current_user, problem_db_id, is_extra=body.is_extra)
    return {"status": progress.status, "solved_at": progress.solved_at.isoformat() if progress.solved_at else None}


@router.post("/problems/{problem_db_id}/deferred")
def mark_deferred(
    problem_db_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    problem = db.get(Problem, problem_db_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    progress = scheduler.mark_problem_deferred(db, current_user, problem_db_id)
    return {"status": progress.status}


@router.post("/problems/{problem_db_id}/needs-revision")
def mark_needs_revision(
    problem_db_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    problem = db.get(Problem, problem_db_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    progress = scheduler.mark_problem_needs_revision(db, current_user, problem_db_id)
    return {"status": progress.status}


# ─── Study Sessions ──────────────────────────────────────────────────────────

@router.post("/study-sessions", status_code=status.HTTP_201_CREATED)
def create_study_session(
    body: StudySessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = streak_svc.record_study_session(
        db=db,
        user=current_user,
        questions_solved=body.questions_solved,
        duration_minutes=body.duration_minutes,
        notes=body.notes,
    )
    streak_info = streak_svc.get_streak_info(db, current_user)
    return {
        "session_id": session.id,
        "session_date": session.session_date,
        "challenge_day": session.challenge_day,
        "questions_solved": session.questions_solved,
        "streak": streak_info,
    }


@router.get("/study-sessions")
def list_study_sessions(
    limit: int = Query(default=14, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = db.execute(
        select(StudySession)
        .where(StudySession.user_id == current_user.id)
        .order_by(StudySession.session_date.desc())
        .limit(limit)
    ).scalars().all()
    return [
        {
            "id": s.id,
            "date": s.session_date,
            "challenge_day": s.challenge_day,
            "questions_solved": s.questions_solved,
            "duration_minutes": s.duration_minutes,
            "notes": s.notes,
            "github_updated": s.github_updated,
            "github_commit_sha": s.github_commit_sha,
        }
        for s in sessions
    ]


# ─── GitHub README Update ────────────────────────────────────────────────────

@router.post("/github/profile-readme")
def update_profile_readme(
    body: GitHubUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the GitHub profile README section for a specific study session."""
    session = db.execute(
        select(StudySession).where(
            StudySession.id == body.session_id,
            StudySession.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    quote = quote_svc.get_quote_for_day(db, session.challenge_day)
    dashboard_url = f"{settings.frontend_url}"

    result = github_service.update_github_profile_readme(
        db=db,
        user=current_user,
        session=session,
        quote=quote,
        dashboard_url=dashboard_url,
        dry_run=body.dry_run,
    )
    return result


# ─── Daily Briefing (for GitHub Actions workflow) ─────────────────────────────

@router.post("/briefing/send")
def send_briefing(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Authenticated, idempotent daily briefing endpoint.
    Called by GitHub Actions workflow — not for browser use.
    """
    from app.services.email_service import send_daily_briefing

    today = scheduler.get_today_ist()
    challenge_day = scheduler.get_challenge_day(settings.challenge_start_date, today)
    assignment = scheduler.get_or_create_daily_assignment(db, current_user)
    stats = scheduler.get_progress_stats(db, current_user)
    streak_info = streak_svc.get_streak_info(db, current_user)
    quote = quote_svc.get_quote_for_day(db, challenge_day)

    from app.models.models import ProblemProgress
    progress_map = {
        p.problem_id: p
        for p in db.execute(
            select(ProblemProgress).where(ProblemProgress.user_id == current_user.id)
        ).scalars().all()
    }

    questions = [_serialize_problem(ap.problem, progress_map) for ap in assignment.problems]

    payload = {
        "challenge_day": challenge_day,
        "date": today,
        "quote": quote,
        "questions": questions,
        "stats": {**stats, **streak_info},
        "dashboard_url": settings.frontend_url,
    }

    result = send_daily_briefing(db=db, user=current_user, payload=payload, delivery_date=today)
    return result
