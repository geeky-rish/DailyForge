"""GitHub profile README update service.

Updates only the section between:
  <!-- DAILYFORGE:START -->
  ...
  <!-- DAILYFORGE:END -->

Rules:
- Fetch latest README before editing (handles conflicts safely).
- Preserve all content outside markers.
- If markers don't exist, safely append the section once.
- Prevent duplicate commits for the same session.
- Dry-run mode shows diff without writing.
- Use meaningful commit message.
- Never create empty/misleading commits.
- Handle API errors and rate limits.
"""
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import GitHubUpdate, StudySession, User

logger = logging.getLogger(__name__)

START_MARKER = "<!-- DAILYFORGE:START -->"
END_MARKER = "<!-- DAILYFORGE:END -->"
GITHUB_API = "https://api.github.com"


def _build_readme_section(session: StudySession, quote: dict, dashboard_url: str) -> str:
    return f"""{START_MARKER}
## ⚔️ DailyForge — DSA Challenge

| 📅 Day | ✅ Solved Today | 🔥 | 💬 Quote |
|--------|----------------|-----|----------|
| **{session.challenge_day}/100** | **{session.questions_solved}** | Keep going! | *"{quote.get('text', ''[:60])}"* |

> "{quote.get('text', '')}" — *{quote.get('author', 'DailyForge')}*

📊 [View Dashboard]({dashboard_url}) | 🗓️ Last updated: {session.session_date}
{END_MARKER}"""


def _inject_section(readme_content: str, new_section: str) -> str:
    """Replace existing section or append if markers absent."""
    pattern = re.compile(
        r"<!-- DAILYFORGE:START -->.*?<!-- DAILYFORGE:END -->",
        re.DOTALL
    )
    if pattern.search(readme_content):
        return pattern.sub(new_section, readme_content)
    # Append
    return readme_content.rstrip() + "\n\n" + new_section + "\n"


def update_github_profile_readme(
    db: Session,
    user: User,
    session: StudySession,
    quote: dict,
    dashboard_url: str,
    dry_run: bool = False,
) -> dict:
    """
    Update the GitHub profile README for the given study session.
    Idempotent: one update per session. dry_run=True shows diff only.
    """
    existing = db.execute(
        select(GitHubUpdate).where(
            GitHubUpdate.user_id == user.id,
            GitHubUpdate.session_id == session.id,
        )
    ).scalar_one_or_none()

    if existing and existing.status in ("success", "dry_run"):
        logger.info("GitHub README already updated for session %d (status=%s)", session.id, existing.status)
        return {
            "status": existing.status,
            "idempotent": True,
            "commit_sha": existing.commit_sha,
            "dry_run": existing.dry_run,
        }

    record = existing or GitHubUpdate(
        user_id=user.id,
        session_id=session.id,
        status="pending",
        dry_run=dry_run,
    )
    if not existing:
        db.add(record)
    db.flush()

    if dry_run:
        new_section = _build_readme_section(session, quote, dashboard_url)
        diff_preview = f"+ {new_section[:200]}"
        logger.info("[DRY RUN] Would update README for session %d:\n%s", session.id, diff_preview)
        record.status = "dry_run"
        record.dry_run = True
        db.commit()
        return {
            "status": "dry_run",
            "idempotent": False,
            "diff_preview": diff_preview,
            "dry_run": True,
        }

    if not settings.github_write_token:
        record.status = "failed"
        record.error_message = "GITHUB_WRITE_TOKEN not configured"
        db.commit()
        raise RuntimeError("GITHUB_WRITE_TOKEN not configured.")

    repo = settings.github_readme_repo  # geeky-rish/geeky-rish
    headers = {
        "Authorization": f"token {settings.github_write_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        # 1. Fetch current README
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{GITHUB_API}/repos/{repo}/contents/README.md", headers=headers)
            if resp.status_code == 404:
                # README doesn't exist — start with empty
                current_content = ""
                sha = None
            elif resp.status_code != 200:
                raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text[:200]}")
            else:
                import base64
                data = resp.json()
                current_content = base64.b64decode(data["content"]).decode("utf-8")
                sha = data["sha"]

        # 2. Build new section and inject
        new_section = _build_readme_section(session, quote, dashboard_url)
        new_content = _inject_section(current_content, new_section)

        # 4. Write to GitHub
        import base64
        encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        commit_payload = {
            "message": f"docs: record DailyForge study session (day {session.challenge_day})",
            "content": encoded,
        }
        if sha:
            commit_payload["sha"] = sha

        with httpx.Client(timeout=30) as client:
            put_resp = client.put(
                f"{GITHUB_API}/repos/{repo}/contents/README.md",
                headers=headers,
                json=commit_payload,
            )
            if put_resp.status_code not in (200, 201):
                raise RuntimeError(f"GitHub write error {put_resp.status_code}: {put_resp.text[:200]}")
            commit_sha = put_resp.json()["commit"]["sha"]

        record.status = "success"
        record.commit_sha = commit_sha
        record.dry_run = False
        db.commit()

        # Also mark session as github_updated
        session.github_updated = True
        session.github_commit_sha = commit_sha
        db.commit()

        logger.info("GitHub README updated for session %d, commit %s", session.id, commit_sha)
        return {"status": "success", "commit_sha": commit_sha, "dry_run": False, "idempotent": False}

    except Exception as exc:
        record.status = "failed"
        record.error_message = str(exc)[:500]
        db.commit()
        logger.error("GitHub README update failed for session %d: %s", session.id, exc)
        raise
