"""Email service — sends daily briefing emails via SMTP.

Supports dry-run mode (logs instead of sending).
Idempotency: checks EmailDelivery table before sending.
Never reports success when email was not actually sent.
"""
import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import EmailDelivery, User

logger = logging.getLogger(__name__)


EMAIL_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>DailyForge Morning Briefing</title></head>
<body style="font-family:sans-serif;max-width:600px;margin:auto;padding:20px;background:#0f0f1a;color:#e2e8f0;">
  <div style="background:linear-gradient(135deg,#1e1b4b,#312e81);border-radius:12px;padding:24px;margin-bottom:20px;">
    <h1 style="color:#a5b4fc;margin:0 0 8px 0;">⚔️ DailyForge</h1>
    <p style="color:#c7d2fe;margin:0;">Day {challenge_day} of 100 &bull; {date}</p>
  </div>

  <div style="background:#1e1e2e;border-radius:8px;padding:20px;margin-bottom:16px;border-left:4px solid #7c3aed;">
    <h2 style="color:#a5b4fc;margin:0 0 12px 0;">💬 Today's Quote</h2>
    <p style="font-style:italic;color:#e2e8f0;font-size:1.1em;">"{quote_text}"</p>
    <p style="color:#94a3b8;margin:0;">— {quote_author}</p>
  </div>

  <div style="background:#1e1e2e;border-radius:8px;padding:20px;margin-bottom:16px;">
    <h2 style="color:#a5b4fc;margin:0 0 12px 0;">📋 Today's Questions</h2>
    {questions_html}
  </div>

  <div style="background:#1e1e2e;border-radius:8px;padding:20px;margin-bottom:16px;">
    <h2 style="color:#a5b4fc;margin:0 0 12px 0;">📊 Progress Summary</h2>
    <table style="width:100%;color:#e2e8f0;">
      <tr><td>✅ Solved</td><td style="text-align:right;color:#4ade80;">{solved}</td></tr>
      <tr><td>🎯 Remaining</td><td style="text-align:right;color:#f59e0b;">{remaining}</td></tr>
      <tr><td>🔥 Current Streak</td><td style="text-align:right;color:#f97316;">{streak} days</td></tr>
      <tr><td>🏆 Longest Streak</td><td style="text-align:right;color:#eab308;">{longest_streak} days</td></tr>
    </table>
  </div>

  <p style="text-align:center;color:#64748b;font-size:0.8em;">
    DailyForge — Striver SDE 180 Tracker<br>
    <a href="{dashboard_url}" style="color:#7c3aed;">Open Dashboard</a>
  </p>
</body>
</html>
"""


def _build_questions_html(questions: list[dict]) -> str:
    items = []
    for i, q in enumerate(questions, 1):
        url = q.get("url", "")
        link = f'<a href="{url}" style="color:#7c3aed;">{q["title"]}</a>' if url else q["title"]
        items.append(
            f'<div style="margin-bottom:12px;padding:12px;background:#2d2d3e;border-radius:6px;">'
            f'<strong style="color:#c7d2fe;">Q{i}.</strong> {link}<br>'
            f'<span style="color:#94a3b8;font-size:0.9em;">{q.get("topic","")} '
            f'{("• " + q["subtopic"]) if q.get("subtopic") else ""} '
            f'{"• " + q["difficulty"] if q.get("difficulty") else ""}</span>'
            f'</div>'
        )
    return "".join(items) if items else "<p style='color:#94a3b8;'>No questions assigned today.</p>"


def send_daily_briefing(
    db: Session,
    user: User,
    payload: dict,
    delivery_date: str,
) -> dict:
    """
    Send (or dry-run) the daily briefing email.
    Idempotent: returns existing delivery record if already sent today.

    payload keys: challenge_day, date, quote, questions, stats, dashboard_url
    """
    existing = db.execute(
        select(EmailDelivery).where(
            EmailDelivery.user_id == user.id,
            EmailDelivery.delivery_date == delivery_date,
        )
    ).scalar_one_or_none()

    if existing and existing.status in ("sent", "dry_run"):
        logger.info("Email already delivered for %s on %s (status=%s)", user.github_username, delivery_date, existing.status)
        return {"status": existing.status, "idempotent": True, "delivery_date": delivery_date}

    # Build record
    record = existing or EmailDelivery(
        user_id=user.id,
        delivery_date=delivery_date,
        status="pending",
    )
    if not existing:
        db.add(record)
    db.flush()

    dry_run = settings.email_dry_run

    # Build content
    questions_html = _build_questions_html(payload.get("questions", []))
    stats = payload.get("stats", {})
    quote = payload.get("quote", {})

    html_body = EMAIL_TEMPLATE.format(
        challenge_day=payload.get("challenge_day", "?"),
        date=delivery_date,
        quote_text=quote.get("text", ""),
        quote_author=quote.get("author", "DailyForge"),
        questions_html=questions_html,
        solved=stats.get("solved", 0),
        remaining=stats.get("remaining", 0),
        streak=stats.get("current_streak", 0),
        longest_streak=stats.get("longest_streak", 0),
        dashboard_url=payload.get("dashboard_url", ""),
    )

    if dry_run:
        logger.info("[DRY RUN] Would send briefing email to %s for %s", settings.email_to, delivery_date)
        record.dry_run = True
        record.status = "dry_run"
        record.sent_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "dry_run", "idempotent": False, "delivery_date": delivery_date}

    # Real send
    sender_user = settings.sender_user
    sender_pass = settings.sender_password
    from_addr = settings.sender_email
    to_addr = settings.recipient

    if not sender_user or not sender_pass or not to_addr:
        record.status = "failed"
        record.error_message = "SMTP credentials or recipient not configured"
        db.commit()
        raise RuntimeError("SMTP credentials not configured. Set SMTP_EMAIL, SMTP_APP_PASSWORD, and RECIPIENT_EMAIL.")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚔️ DailyForge Day {payload.get('challenge_day', '?')} — Morning Briefing"
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            if settings.smtp_tls:
                smtp.starttls()
            smtp.login(sender_user, sender_pass)
            smtp.sendmail(from_addr, [to_addr], msg.as_string())

        record.status = "sent"
        record.sent_at = datetime.now(timezone.utc)
        record.dry_run = False
        db.commit()
        logger.info("Email sent successfully to %s for %s", to_addr, delivery_date)
        return {"status": "sent", "idempotent": False, "delivery_date": delivery_date}

    except Exception as exc:
        record.status = "failed"
        record.error_message = str(exc)[:500]
        db.commit()
        logger.error("Failed to send email for %s: %s", delivery_date, exc)
        raise
