"""Authentication dependency — extracts and validates the current user from cookie."""
import logging
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User

logger = logging.getLogger(__name__)


def get_current_user(
    session_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Extract authenticated user from HTTP-only session cookie."""
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(session_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    github_id: Optional[int] = payload.get("github_id")
    if not github_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Validate against authorized user ID (not username from browser)
    if settings.authorized_github_user_id and github_id != settings.authorized_github_user_id:
        logger.warning("Unauthorized access attempt by github_id=%s", github_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    user = db.execute(
        select(User).where(User.github_id == github_id)
    ).scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user
