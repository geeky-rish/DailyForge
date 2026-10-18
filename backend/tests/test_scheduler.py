"""Tests for question scheduling service — covers all business rules."""
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from app.services.scheduler import (
    get_or_create_daily_assignment,
    get_challenge_day,
    mark_problem_attempted,
    mark_problem_solved,
    mark_problem_deferred,
    mark_problem_needs_revision,
    get_progress_stats,
    get_today_ist,
)
from app.models.models import DailyAssignment, ProblemProgress


class TestChallengeDayCalculation:
    def test_day_one_is_start_date(self):
        assert get_challenge_day("2024-01-01", "2024-01-01") == 1

    def test_day_two_next_day(self):
        assert get_challenge_day("2024-01-01", "2024-01-02") == 2

    def test_day_100_after_99_days(self):
        assert get_challenge_day("2024-01-01", "2024-04-09") == 100

    def test_before_start_date_returns_one(self):
        assert get_challenge_day("2024-01-01", "2023-12-31") == 1


class TestDailyAssignment:
    def test_creates_assignment_with_two_problems(self, db, test_user, sample_problems):
        assignment = get_or_create_daily_assignment(db, test_user)
        assert len(assignment.problems) == 2

    def test_idempotent_same_day(self, db, test_user, sample_problems):
        """Calling twice on same day must not create duplicate."""
        a1 = get_or_create_daily_assignment(db, test_user)
        a2 = get_or_create_daily_assignment(db, test_user)
        assert a1.id == a2.id

    def test_assignment_uses_sheet_order(self, db, test_user, sample_problems):
        """First assignment should use problems with lowest sheet_order."""
        assignment = get_or_create_daily_assignment(db, test_user)
        orders = [ap.problem.sheet_order for ap in assignment.problems]
        assert sorted(orders) == orders  # ascending order

    def test_solved_problems_excluded(self, db, test_user, sample_problems):
        """Solved problems must not appear in daily assignment."""
        # Solve the first two problems
        for p in sample_problems[:2]:
            mark_problem_solved(db, test_user, p.id)

        with patch("app.services.scheduler.get_today_ist", return_value="2024-01-02"):
            assignment = get_or_create_daily_assignment(db, test_user)

        problem_ids = {ap.problem_id for ap in assignment.problems}
        solved_ids = {p.id for p in sample_problems[:2]}
        assert problem_ids.isdisjoint(solved_ids)

    def test_extra_questions_do_not_reduce_next_day(self, db, test_user, sample_problems):
        """Solving 3+ questions today must not reduce tomorrow's target of 2."""
        # Day 1: assign 2 problems
        with patch("app.services.scheduler.get_today_ist", return_value="2024-01-01"):
            a1 = get_or_create_daily_assignment(db, test_user)

        # Solve all assigned + 2 extra
        for i, ap in enumerate(a1.problems):
            mark_problem_solved(db, test_user, ap.problem_id)

        # Extra problems solved (outside assignment)
        for p in sample_problems[2:4]:
            mark_problem_solved(db, test_user, p.id, is_extra=True)

        # Day 2: should still get 2 fresh problems
        with patch("app.services.scheduler.get_today_ist", return_value="2024-01-02"):
            a2 = get_or_create_daily_assignment(db, test_user)

        assert len(a2.problems) == 2

    def test_no_duplicate_problems_across_days(self, db, test_user, sample_problems):
        """Problems assigned on day 1 must not appear in day 2 assignment."""
        with patch("app.services.scheduler.get_today_ist", return_value="2024-01-01"):
            a1 = get_or_create_daily_assignment(db, test_user)

        day1_ids = {ap.problem_id for ap in a1.problems}

        with patch("app.services.scheduler.get_today_ist", return_value="2024-01-02"):
            a2 = get_or_create_daily_assignment(db, test_user)

        day2_ids = {ap.problem_id for ap in a2.problems}
        assert day1_ids.isdisjoint(day2_ids)

    def test_completion_state_when_all_solved(self, db, test_user, sample_problems):
        """When all problems solved, assignment has 0 new problems."""
        # Solve all 10
        for p in sample_problems:
            mark_problem_solved(db, test_user, p.id)

        with patch("app.services.scheduler.get_today_ist", return_value="2024-01-06"):
            assignment = get_or_create_daily_assignment(db, test_user)

        assert len(assignment.problems) == 0

    def test_missed_days_dont_create_false_assignments(self, db, test_user, sample_problems):
        """Missed days do not get auto-assigned retroactively."""
        with patch("app.services.scheduler.get_today_ist", return_value="2024-01-10"):
            a = get_or_create_daily_assignment(db, test_user)
        
        # Only one assignment should exist
        total = db.query(DailyAssignment).filter(DailyAssignment.user_id == test_user.id).count()
        assert total == 1


class TestProblemStatusMutations:
    def test_attempted_does_not_mark_solved(self, db, test_user, sample_problems):
        """Marking attempted must NOT change status to solved."""
        p = sample_problems[0]
        progress = mark_problem_attempted(db, test_user, p.id)
        assert progress.status == "attempted"
        assert progress.solved_at is None

    def test_attempted_increments_attempts(self, db, test_user, sample_problems):
        p = sample_problems[0]
        mark_problem_attempted(db, test_user, p.id)
        progress = mark_problem_attempted(db, test_user, p.id)
        assert progress.attempts == 2

    def test_solved_sets_solved_at(self, db, test_user, sample_problems):
        p = sample_problems[0]
        progress = mark_problem_solved(db, test_user, p.id)
        assert progress.status == "solved"
        assert progress.solved_at is not None

    def test_solved_does_not_overwrite_solved_at_on_retry(self, db, test_user, sample_problems):
        p = sample_problems[0]
        p1 = mark_problem_solved(db, test_user, p.id)
        first_time = p1.solved_at
        p2 = mark_problem_solved(db, test_user, p.id)
        assert p2.solved_at == first_time

    def test_deferred_status(self, db, test_user, sample_problems):
        p = sample_problems[0]
        progress = mark_problem_deferred(db, test_user, p.id)
        assert progress.status == "deferred"

    def test_needs_revision_status(self, db, test_user, sample_problems):
        p = sample_problems[0]
        progress = mark_problem_needs_revision(db, test_user, p.id)
        assert progress.status == "needs_revision"

    def test_extra_flag_tracking(self, db, test_user, sample_problems):
        p = sample_problems[0]
        progress = mark_problem_solved(db, test_user, p.id, is_extra=True)
        assert progress.is_extra is True


class TestProgressStats:
    def test_initial_stats(self, db, test_user, sample_problems):
        stats = get_progress_stats(db, test_user)
        assert stats["total"] == 10
        assert stats["solved"] == 0
        assert stats["remaining"] == 10
        assert stats["is_complete"] is False

    def test_stats_after_solving(self, db, test_user, sample_problems):
        mark_problem_solved(db, test_user, sample_problems[0].id)
        mark_problem_solved(db, test_user, sample_problems[1].id)
        stats = get_progress_stats(db, test_user)
        assert stats["solved"] == 2
        assert stats["remaining"] == 8

    def test_completion_state(self, db, test_user, sample_problems):
        for p in sample_problems:
            mark_problem_solved(db, test_user, p.id)
        stats = get_progress_stats(db, test_user)
        assert stats["is_complete"] is True
        assert stats["remaining"] == 0
