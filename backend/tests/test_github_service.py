"""Tests for GitHub README update service — uses fixtures, no real GitHub API calls."""
import pytest
from unittest.mock import patch, MagicMock

from app.services.github_service import _inject_section, _build_readme_section, START_MARKER, END_MARKER
from app.models.models import StudySession, GitHubUpdate


class TestReadmeMarkerInjection:
    def test_replaces_existing_section(self):
        readme = "# My Profile\n\n<!-- DAILYFORGE:START -->\nOld content\n<!-- DAILYFORGE:END -->\n\n## Other Section\nContent here."
        new_section = "<!-- DAILYFORGE:START -->\nNew content\n<!-- DAILYFORGE:END -->"
        result = _inject_section(readme, new_section)
        assert "New content" in result
        assert "Old content" not in result
        assert "## Other Section" in result  # preserved outside section

    def test_appends_when_markers_absent(self):
        readme = "# My Profile\n\nSome content.\n\n## Projects\nList here."
        new_section = "<!-- DAILYFORGE:START -->\nDailyForge content\n<!-- DAILYFORGE:END -->"
        result = _inject_section(readme, new_section)
        assert "DailyForge content" in result
        assert "## Projects" in result  # preserved
        assert "Some content." in result  # preserved

    def test_preserves_content_before_markers(self):
        readme = "# Header\n\nBefore content.\n\n<!-- DAILYFORGE:START -->\nOld\n<!-- DAILYFORGE:END -->\n\nAfter content."
        new_section = "<!-- DAILYFORGE:START -->\nNew\n<!-- DAILYFORGE:END -->"
        result = _inject_section(readme, new_section)
        assert "Before content." in result
        assert "After content." in result

    def test_preserves_content_after_markers(self):
        readme = "# H\n<!-- DAILYFORGE:START -->\nOld\n<!-- DAILYFORGE:END -->\n\n## Footer\nFooter content."
        new_section = "<!-- DAILYFORGE:START -->\nNew\n<!-- DAILYFORGE:END -->"
        result = _inject_section(readme, new_section)
        assert "## Footer" in result
        assert "Footer content." in result

    def test_start_marker_present_end_marker_present(self):
        readme = f"{START_MARKER}\nSome content\n{END_MARKER}"
        new_section = f"{START_MARKER}\nReplaced\n{END_MARKER}"
        result = _inject_section(readme, new_section)
        assert "Replaced" in result
        assert "Some content" not in result

    def test_empty_readme_append(self):
        result = _inject_section("", "<!-- DAILYFORGE:START -->\nContent\n<!-- DAILYFORGE:END -->")
        assert "Content" in result


class TestReadmeSectionBuilding:
    def test_section_contains_markers(self):
        session = MagicMock()
        session.challenge_day = 42
        session.questions_solved = 3
        session.session_date = "2024-02-11"
        quote = {"text": "Test quote", "author": "Test Author"}
        section = _build_readme_section(session, quote, "https://example.com")
        assert START_MARKER in section
        assert END_MARKER in section

    def test_section_contains_challenge_day(self):
        session = MagicMock()
        session.challenge_day = 42
        session.questions_solved = 2
        session.session_date = "2024-02-11"
        quote = {"text": "Go", "author": "Author"}
        section = _build_readme_section(session, quote, "https://example.com")
        assert "42" in section

    def test_section_contains_quote(self):
        session = MagicMock()
        session.challenge_day = 1
        session.questions_solved = 2
        session.session_date = "2024-01-01"
        quote = {"text": "Unique test quote text", "author": "Author"}
        section = _build_readme_section(session, quote, "https://example.com")
        assert "Unique test quote text" in section


class TestGitHubUpdateIdempotency:
    def test_dry_run_does_not_call_github_api(self, db, test_user):
        """Dry run must not make any real HTTP calls."""
        session = StudySession(
            user_id=test_user.id,
            session_date="2024-01-01",
            challenge_day=1,
            questions_solved=2,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        quote = {"text": "Test", "author": "Author"}
        with patch("app.services.github_service.httpx.Client") as mock_client:
            from app.services.github_service import update_github_profile_readme
            result = update_github_profile_readme(
                db=db, user=test_user, session=session,
                quote=quote, dashboard_url="http://localhost:5173",
                dry_run=True,
            )
        # HTTP client must not have been called
        mock_client.assert_not_called()
        assert result["status"] == "dry_run"

    def test_idempotent_on_second_call(self, db, test_user):
        """Second call for same session returns idempotent result."""
        session = StudySession(
            user_id=test_user.id,
            session_date="2024-01-01",
            challenge_day=1,
            questions_solved=2,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        quote = {"text": "Test", "author": "Author"}
        from app.services.github_service import update_github_profile_readme

        # First call dry_run
        r1 = update_github_profile_readme(
            db=db, user=test_user, session=session,
            quote=quote, dashboard_url="http://localhost:5173",
            dry_run=True,
        )
        # Second call
        r2 = update_github_profile_readme(
            db=db, user=test_user, session=session,
            quote=quote, dashboard_url="http://localhost:5173",
            dry_run=True,
        )
        assert r2["idempotent"] is True
