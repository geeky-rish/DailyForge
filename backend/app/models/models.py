"""All SQLAlchemy ORM models for DailyForge."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    github_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    github_username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    github_avatar_url: Mapped[Optional[str]] = mapped_column(String(512))
    github_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    progress: Mapped[list["ProblemProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    study_sessions: Mapped[list["StudySession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    daily_assignments: Mapped[list["DailyAssignment"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    problem_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    sheet_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    subtopic: Mapped[Optional[str]] = mapped_column(String(128))
    difficulty: Mapped[Optional[str]] = mapped_column(String(32))
    url: Mapped[Optional[str]] = mapped_column(String(1024))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    progress: Mapped[list["ProblemProgress"]] = relationship(back_populates="problem", cascade="all, delete-orphan")
    assignments: Mapped[list["DailyAssignmentProblem"]] = relationship(back_populates="problem")


class ProblemProgress(Base):
    """Per-user progress on a specific problem."""
    __tablename__ = "problem_progress"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", name="uq_user_problem"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False, index=True)
    # Status: unsolved | attempted | solved | deferred | needs_revision
    status: Mapped[str] = mapped_column(String(32), default="unsolved", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    solved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deferred_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_extra: Mapped[bool] = mapped_column(Boolean, default=False)  # solved outside daily assignment

    user: Mapped["User"] = relationship(back_populates="progress")
    problem: Mapped["Problem"] = relationship(back_populates="progress")


class DailyAssignment(Base):
    """One record per user per calendar day (Asia/Kolkata date)."""
    __tablename__ = "daily_assignments"
    __table_args__ = (UniqueConstraint("user_id", "assignment_date", name="uq_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    assignment_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD IST
    challenge_day: Mapped[int] = mapped_column(Integer, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="daily_assignments")
    problems: Mapped[list["DailyAssignmentProblem"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )


class DailyAssignmentProblem(Base):
    """Junction: which problems belong to a given daily assignment."""
    __tablename__ = "daily_assignment_problems"
    __table_args__ = (UniqueConstraint("assignment_id", "problem_id", name="uq_assignment_problem"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("daily_assignments.id"), nullable=False, index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)  # order within day

    assignment: Mapped["DailyAssignment"] = relationship(back_populates="problems")
    problem: Mapped["Problem"] = relationship(back_populates="assignments")


class StudySession(Base):
    """A genuine, recorded study session for streak calculation."""
    __tablename__ = "study_sessions"
    __table_args__ = (UniqueConstraint("user_id", "session_date", name="uq_user_session_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    session_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD IST
    challenge_day: Mapped[int] = mapped_column(Integer, nullable=False)
    questions_solved: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    github_updated: Mapped[bool] = mapped_column(Boolean, default=False)
    github_commit_sha: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="study_sessions")


class ChallengeState(Base):
    """Per-user overall challenge state."""
    __tablename__ = "challenge_states"
    __table_args__ = (UniqueConstraint("user_id", name="uq_challenge_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    start_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_session_date: Mapped[Optional[str]] = mapped_column(String(10))
    total_solved: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DailyQuoteSelection(Base):
    """Persisted quote selection per challenge-day (stable across restarts)."""
    __tablename__ = "daily_quote_selections"
    __table_args__ = (UniqueConstraint("challenge_day", name="uq_quote_challenge_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    challenge_day: Mapped[int] = mapped_column(Integer, nullable=False)
    quote_text: Mapped[str] = mapped_column(Text, nullable=False)
    quote_author: Mapped[str] = mapped_column(String(256), nullable=False)
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmailDelivery(Base):
    """Idempotency record for daily briefing emails."""
    __tablename__ = "email_deliveries"
    __table_args__ = (UniqueConstraint("user_id", "delivery_date", name="uq_email_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    delivery_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending | sent | failed | dry_run
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class GitHubUpdate(Base):
    """Idempotency record for GitHub README updates."""
    __tablename__ = "github_updates"
    __table_args__ = (UniqueConstraint("user_id", "session_id", name="uq_github_update_session"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    session_id: Mapped[int] = mapped_column(ForeignKey("study_sessions.id"), nullable=False)
    commit_sha: Mapped[Optional[str]] = mapped_column(String(64))
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending | success | failed | dry_run
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
