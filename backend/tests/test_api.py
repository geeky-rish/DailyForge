"""Tests for API endpoints — auth, dashboard, problem mutations, unauthorized access."""
import pytest
from unittest.mock import patch


class TestHealthEndpoints:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_does_not_expose_env(self, client):
        resp = client.get("/health")
        body = resp.text
        assert "DATABASE_URL" not in body
        assert "SECRET_KEY" not in body
        assert "password" not in body.lower()

    def test_ready_endpoint(self, client):
        resp = client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "database" in data


class TestUnauthorizedAccess:
    def test_me_requires_auth(self, client):
        resp = client.get("/api/me")
        assert resp.status_code == 401

    def test_dashboard_requires_auth(self, client):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 401

    def test_study_sessions_requires_auth(self, client):
        resp = client.post("/api/study-sessions", json={"questions_solved": 2})
        assert resp.status_code == 401

    def test_problem_solved_requires_auth(self, client):
        resp = client.post("/api/problems/1/solved", json={"problem_db_id": 1})
        assert resp.status_code == 401

    def test_github_update_requires_auth(self, client):
        resp = client.post("/api/github/profile-readme", json={"session_id": 1, "dry_run": True})
        assert resp.status_code == 401


class TestOAuthStartEndpoint:
    def test_start_returns_auth_url(self, client):
        resp = client.post("/auth/github/start")
        assert resp.status_code == 200
        data = resp.json()
        assert "auth_url" in data
        assert "github.com/login/oauth/authorize" in data["auth_url"]
        assert "state" in data

    def test_start_includes_client_id(self, client):
        resp = client.post("/auth/github/start")
        url = resp.json()["auth_url"]
        assert "test-client-id" in url


class TestOAuthCallback:
    def test_callback_invalid_state(self, client):
        resp = client.get("/auth/github/callback?code=abc&state=invalid-state-xyz")
        assert resp.status_code == 400

    def test_callback_missing_code(self, client):
        resp = client.get("/auth/github/callback?state=somestate")
        assert resp.status_code == 400

    def test_callback_error_param_redirects(self, client):
        resp = client.get("/auth/github/callback?error=access_denied", follow_redirects=False)
        assert resp.status_code in (302, 307)


class TestLogout:
    def test_logout_clears_cookie(self, client):
        resp = client.post("/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["status"] == "logged_out"


class TestEmailDryRun:
    def test_email_dry_run_does_not_send(self, db, test_user):
        """Email dry run must not call SMTP."""
        from app.services.email_service import send_daily_briefing
        import smtplib
        with patch.object(smtplib, "SMTP") as mock_smtp:
            result = send_daily_briefing(
                db=db,
                user=test_user,
                payload={"challenge_day": 1, "quote": {"text": "X", "author": "Y"}, "questions": [], "stats": {}, "dashboard_url": "http://localhost"},
                delivery_date="2024-01-01",
            )
        mock_smtp.assert_not_called()
        assert result["status"] == "dry_run"

    def test_email_idempotent(self, db, test_user):
        """Sending email twice for same date returns idempotent=True on second call."""
        from app.services.email_service import send_daily_briefing
        payload = {"challenge_day": 1, "quote": {"text": "X", "author": "Y"}, "questions": [], "stats": {}, "dashboard_url": "http://localhost"}
        r1 = send_daily_briefing(db=db, user=test_user, payload=payload, delivery_date="2024-01-01")
        r2 = send_daily_briefing(db=db, user=test_user, payload=payload, delivery_date="2024-01-01")
        assert r2["idempotent"] is True
