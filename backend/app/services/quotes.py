"""Quote service — selects and persists daily quotes.

The quote for a given challenge day is selected once and persisted,
so backend restarts cannot change it.
"""
import json
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import DailyQuoteSelection

logger = logging.getLogger(__name__)

_QUOTES_PATH = Path(__file__).parent.parent.parent.parent / "data" / "quotes" / "quotes.json"


def _load_quotes() -> list[dict]:
    if _QUOTES_PATH.exists():
        with open(_QUOTES_PATH, encoding="utf-8") as f:
            return json.load(f)
    logger.warning("quotes.json not found at %s", _QUOTES_PATH)
    return []


def get_quote_for_day(db: Session, challenge_day: int) -> dict:
    """
    Return the persisted quote for the given challenge day.
    If not yet persisted, select from the dataset and save it.
    """
    existing = db.execute(
        select(DailyQuoteSelection).where(DailyQuoteSelection.challenge_day == challenge_day)
    ).scalar_one_or_none()

    if existing:
        return {"day": challenge_day, "text": existing.quote_text, "author": existing.quote_author}

    # Select quote from dataset (use modulo for days > 100)
    quotes = _load_quotes()
    if not quotes:
        fallback = {"day": challenge_day, "text": "Keep coding. Keep growing.", "author": "DailyForge"}
        return fallback

    # Use (day - 1) % len(quotes) so day 1 maps to index 0
    idx = (challenge_day - 1) % len(quotes)
    quote = quotes[idx]

    selection = DailyQuoteSelection(
        challenge_day=challenge_day,
        quote_text=quote["text"],
        quote_author=quote.get("author", "DailyForge"),
    )
    db.add(selection)
    db.commit()
    db.refresh(selection)

    return {"day": challenge_day, "text": selection.quote_text, "author": selection.quote_author}
