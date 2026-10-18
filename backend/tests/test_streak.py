"""Tests for streak calculation service."""
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from app.services.streak import record_study_session, get_streak_info
from app.models.models import ChallengeState


class TestStudySessionRecording:
    def test_records_session(self, db, test_user):
        with patch("app.services.streak.get_today_ist", return_value="2024-01-01"):
            session = record_study_session(db, test_user, questions_solved=2)
        assert session.session_date == "2024-01-01"
        assert session.questions_solved == 2

    def test_idempotent_same_day(self, db, test_user):
        """Recording twice same day returns same session."""
        with patch("app.services.streak.get_today_ist", return_value="2024-01-01"):
            s1 = record_study_session(db, test_user, questions_solved=2)
            s2 = record_study_session(db, test_user, questions_solved=5)  # different count
        assert s1.id == s2.id
        assert s1.questions_solved == 2  # original count preserved

    def test_challenge_day_recorded(self, db, test_user):
        with patch("app.services.streak.get_today_ist", return_value="2024-01-01"):
            session = record_study_session(db, test_user, questions_solved=2)
        assert session.challenge_day >= 1


class TestStreakCalculation:
    def test_initial_streak_is_one(self, db, test_user):
        with patch("app.services.streak.get_today_ist", return_value="2024-01-01"):
            record_study_session(db, test_user, questions_solved=2)
        info = get_streak_info(db, test_user)
        assert info["current_streak"] == 1
        assert info["longest_streak"] == 1

    def test_consecutive_days_increment_streak(self, db, test_user):
        for i in range(5):
            day = f"2024-01-{i+1:02d}"
            with patch("app.services.streak.get_today_ist", return_value=day):
                record_study_session(db, test_user, questions_solved=2)
        info = get_streak_info(db, test_user)
        assert info["current_streak"] == 5
        assert info["longest_streak"] == 5

    def test_missed_day_resets_streak(self, db, test_user):
        """A gap in sessions resets current streak."""
        for day in ["2024-01-01", "2024-01-02", "2024-01-03"]:
            with patch("app.services.streak.get_today_ist", return_value=day):
                record_study_session(db, test_user, questions_solved=2)
        # Miss day 4, record day 5
        with patch("app.services.streak.get_today_ist", return_value="2024-01-05"):
            record_study_session(db, test_user, questions_solved=2)
        info = get_streak_info(db, test_user)
        assert info["current_streak"] == 1  # reset after gap
        assert info["longest_streak"] == 3  # preserved

    def test_streak_not_incremented_same_date_twice(self, db, test_user):
        """Calling record twice on same day must not double the streak."""
        with patch("app.services.streak.get_today_ist", return_value="2024-01-01"):
            record_study_session(db, test_user, questions_solved=2)
            record_study_session(db, test_user, questions_solved=2)  # idempotent
        info = get_streak_info(db, test_user)
        assert info["current_streak"] == 1

    def test_longest_streak_preserved_after_reset(self, db, test_user):
        """longest_streak must survive a reset."""
        for day in ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]:
            with patch("app.services.streak.get_today_ist", return_value=day):
                record_study_session(db, test_user, questions_solved=2)
        # Gap + new session
        with patch("app.services.streak.get_today_ist", return_value="2024-01-10"):
            record_study_session(db, test_user, questions_solved=2)
        info = get_streak_info(db, test_user)
        assert info["current_streak"] == 1
        assert info["longest_streak"] == 5

    def test_no_sessions_returns_zero_streak(self, db, test_user):
        info = get_streak_info(db, test_user)
        assert info["current_streak"] == 0
        assert info["longest_streak"] == 0
