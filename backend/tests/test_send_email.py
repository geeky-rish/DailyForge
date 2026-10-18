"""Unit tests for standalone Gmail SMTP email sender (backend/scripts/send_email.py)."""

import os
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from scripts.send_email import (
    get_recipient_email,
    get_sender_email,
    get_smtp_password,
    send_smtp_email,
)


def test_get_sender_email_from_param():
    assert get_sender_email("user@example.com") == "user@example.com"


def test_get_sender_email_from_env(monkeypatch):
    monkeypatch.setenv("SMTP_EMAIL", "learn.rishipk@gmail.com")
    assert get_sender_email() == "learn.rishipk@gmail.com"


def test_get_sender_email_missing(monkeypatch):
    monkeypatch.delenv("SMTP_EMAIL", raising=False)
    monkeypatch.delenv("EMAIL_FROM", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    with pytest.raises(ValueError, match="Missing sender email"):
        get_sender_email()


def test_get_recipient_email_from_env(monkeypatch):
    monkeypatch.setenv("RECIPIENT_EMAIL", "hello.rishikulkarni@gmail.com")
    assert get_recipient_email() == "hello.rishikulkarni@gmail.com"


def test_get_recipient_email_missing(monkeypatch):
    monkeypatch.delenv("RECIPIENT_EMAIL", raising=False)
    monkeypatch.delenv("EMAIL_TO", raising=False)
    with pytest.raises(ValueError, match="Missing recipient email"):
        get_recipient_email()


def test_get_smtp_password_from_env(monkeypatch):
    monkeypatch.setenv("SMTP_APP_PASSWORD", "secret_pass_123")
    assert get_smtp_password() == "secret_pass_123"


def test_get_smtp_password_missing(monkeypatch):
    monkeypatch.delenv("SMTP_APP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    with pytest.raises(ValueError, match="Missing SMTP password"):
        get_smtp_password()


def test_send_smtp_email_success(monkeypatch):
    monkeypatch.setenv("SMTP_EMAIL", "learn.rishipk@gmail.com")
    monkeypatch.setenv("SMTP_APP_PASSWORD", "secret_token")
    monkeypatch.setenv("RECIPIENT_EMAIL", "hello.rishikulkarni@gmail.com")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        result = send_smtp_email(
            subject="DailyForge SMTP Test",
            body="Your DailyForge email delivery is working.",
        )

        assert result["status"] == "success"
        assert result["sender"] == "learn.rishipk@gmail.com"
        assert result["recipient"] == "hello.rishikulkarni@gmail.com"

        mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 587, timeout=30)
        assert mock_server.ehlo.call_count == 2
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("learn.rishipk@gmail.com", "secret_token")
        mock_server.send_message.assert_called_once()


def test_send_smtp_email_auth_failure(monkeypatch):
    monkeypatch.setenv("SMTP_EMAIL", "learn.rishipk@gmail.com")
    monkeypatch.setenv("SMTP_APP_PASSWORD", "bad_token")
    monkeypatch.setenv("RECIPIENT_EMAIL", "hello.rishikulkarni@gmail.com")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication credentials invalid")
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        with pytest.raises(RuntimeError, match="SMTP authentication failed"):
            send_smtp_email(
                subject="DailyForge SMTP Test",
                body="Your DailyForge email delivery is working.",
            )
