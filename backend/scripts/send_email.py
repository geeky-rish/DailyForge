#!/usr/bin/env python3
"""Reusable Gmail SMTP Email Sender for DailyForge.

Connects to smtp.gmail.com over port 587 using STARTTLS.
Reads credentials securely from environment variables:
  - SMTP_EMAIL (sender email, e.g. learn.rishipk@gmail.com)
  - SMTP_APP_PASSWORD (Gmail App Password)
  - RECIPIENT_EMAIL (recipient email, e.g. hello.rishikulkarni@gmail.com)

Supports CLI execution and direct module import without requiring
database or backend dependencies. Never prints or leaks credentials in logs.
"""

from __future__ import annotations

import argparse
import logging
import os
import smtplib
import ssl
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dailyforge.smtp")


def get_sender_email(explicit_sender: Optional[str] = None) -> str:
    """Resolve sender email from arguments or environment variables."""
    sender = (
        explicit_sender
        or os.getenv("SMTP_EMAIL")
        or os.getenv("EMAIL_FROM")
        or os.getenv("SMTP_USER")
    )
    if not sender or not sender.strip():
        raise ValueError(
            "Missing sender email. Please provide --sender or set the SMTP_EMAIL "
            "(or EMAIL_FROM / SMTP_USER) environment variable."
        )
    return sender.strip()


def get_recipient_email(explicit_recipient: Optional[str] = None) -> str:
    """Resolve recipient email from arguments or environment variables."""
    recipient = (
        explicit_recipient
        or os.getenv("RECIPIENT_EMAIL")
        or os.getenv("EMAIL_TO")
    )
    if not recipient or not recipient.strip():
        raise ValueError(
            "Missing recipient email. Please provide --recipient or set the "
            "RECIPIENT_EMAIL (or EMAIL_TO) environment variable."
        )
    return recipient.strip()


def get_smtp_password(explicit_password: Optional[str] = None) -> str:
    """Resolve SMTP App Password from arguments or environment variables."""
    password = (
        explicit_password
        or os.getenv("SMTP_APP_PASSWORD")
        or os.getenv("SMTP_PASSWORD")
    )
    if not password or not password.strip():
        raise ValueError(
            "Missing SMTP password. Please set the SMTP_APP_PASSWORD "
            "(or SMTP_PASSWORD) environment variable."
        )
    # Strip whitespace/newlines that might accidentally get pasted
    return password.strip()


def send_smtp_email(
    subject: str,
    body: str,
    recipient: Optional[str] = None,
    sender: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    use_tls: bool = True,
    is_html: bool = False,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Send an email using Gmail SMTP with STARTTLS.

    Args:
        subject: Email subject line.
        body: Email text or HTML body.
        recipient: Destination email address (falls back to RECIPIENT_EMAIL / EMAIL_TO).
        sender: Sender email address (falls back to SMTP_EMAIL / EMAIL_FROM / SMTP_USER).
        password: SMTP App Password (falls back to SMTP_APP_PASSWORD / SMTP_PASSWORD).
        host: SMTP host (defaults to SMTP_HOST env or 'smtp.gmail.com').
        port: SMTP port (defaults to SMTP_PORT env or 587).
        use_tls: Whether to use STARTTLS (defaults to True).
        is_html: Whether body content is HTML (defaults to False).
        timeout: Socket timeout in seconds (defaults to 30).

    Returns:
        Dict containing status, recipient, sender, and subject.
    """
    resolved_sender = get_sender_email(sender)
    resolved_recipient = get_recipient_email(recipient)
    resolved_password = get_smtp_password(password)

    resolved_host = host or os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    try:
        resolved_port = int(port or os.getenv("SMTP_PORT", "587"))
    except ValueError:
        resolved_port = 587

    logger.info(
        "Preparing email delivery: from='%s' to='%s' via %s:%d (STARTTLS=%s)",
        resolved_sender,
        resolved_recipient,
        resolved_host,
        resolved_port,
        use_tls,
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = resolved_sender
    msg["To"] = resolved_recipient

    subtype = "html" if is_html else "plain"
    msg.attach(MIMEText(body, subtype, "utf-8"))

    try:
        with smtplib.SMTP(resolved_host, resolved_port, timeout=timeout) as server:
            server.ehlo()
            if use_tls:
                ssl_context = ssl.create_default_context()
                server.starttls(context=ssl_context)
                server.ehlo()

            # Authenticate with credentials
            server.login(resolved_sender, resolved_password)
            server.send_message(msg)

        logger.info(
            "[SUCCESS] Email successfully sent to '%s' with subject '%s'",
            resolved_recipient,
            subject,
        )
        return {
            "status": "success",
            "sender": resolved_sender,
            "recipient": resolved_recipient,
            "subject": subject,
            "host": resolved_host,
            "port": resolved_port,
        }

    except smtplib.SMTPAuthenticationError as auth_err:
        logger.error(
            "[FAILURE] SMTP authentication failed: Check your email and Google App Password."
        )
        raise RuntimeError(
            "SMTP authentication failed. Verify SMTP_EMAIL and SMTP_APP_PASSWORD."
        ) from auth_err

    except smtplib.SMTPException as smtp_err:
        logger.error("[FAILURE] SMTP error occurred during transmission: %s", smtp_err)
        raise RuntimeError(f"SMTP error: {smtp_err}") from smtp_err

    except Exception as exc:
        logger.error("[FAILURE] Unexpected error sending email: %s", exc)
        raise


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DailyForge Gmail SMTP Email Sender",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--subject",
        default="DailyForge SMTP Test",
        help="Email subject",
    )
    parser.add_argument(
        "--body",
        default="Your DailyForge email delivery is working.",
        help="Email body text",
    )
    parser.add_argument(
        "--recipient",
        "--to",
        dest="recipient",
        default=None,
        help="Recipient email address (defaults to RECIPIENT_EMAIL or EMAIL_TO env)",
    )
    parser.add_argument(
        "--sender",
        "--from",
        dest="sender",
        default=None,
        help="Sender email address (defaults to SMTP_EMAIL or EMAIL_FROM env)",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Treat the body as HTML instead of plain text",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="SMTP server hostname (defaults to SMTP_HOST env or smtp.gmail.com)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="SMTP server port (defaults to SMTP_PORT env or 587)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and inputs without opening an SMTP connection",
    )
    return parser.parse_args()


def main() -> int:
    """Main CLI entrypoint."""
    args = parse_args()

    try:
        if args.dry_run:
            sender = get_sender_email(args.sender)
            recipient = get_recipient_email(args.recipient)
            get_smtp_password()
            logger.info(
                "[DRY-RUN] Credentials and parameters validated successfully. "
                "Sender: '%s', Recipient: '%s', Subject: '%s'",
                sender,
                recipient,
                args.subject,
            )
            return 0

        send_smtp_email(
            subject=args.subject,
            body=args.body,
            recipient=args.recipient,
            sender=args.sender,
            host=args.host,
            port=args.port,
            is_html=args.html,
        )
        print("\n[DAILYFORGE SMTP] SUCCESS: Test email delivered successfully.")
        return 0

    except Exception as exc:
        print(f"\n[DAILYFORGE SMTP] FAILURE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
