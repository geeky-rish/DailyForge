"""GitHub OAuth authentication router.

Flow:
1. POST /auth/github/start  → redirect to GitHub with random state
2. GET  /auth/github/callback → validate state, exchange code, verify user ID
3. POST /auth/logout         → clear session cookie
"""
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, generate_oauth_state
from app.models.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

# In-memory state store (acceptable for single-user app; replace with Redis for multi-user)
_oauth_states: dict[str, float] = {}


def get_redirect_uri(request: Request) -> str:
    """Resolve the OAuth redirect URI matching the active host."""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    proto = request.headers.get("x-forwarded-proto", "https")
    if "onrender.com" in host:
        return f"{proto}://{host}/auth/github/callback"
    if settings.github_redirect_uri and "localhost" not in settings.github_redirect_uri and "dailyforge-backend.onrender.com" not in settings.github_redirect_uri:
        return settings.github_redirect_uri
    if host:
        return f"{proto}://{host}/auth/github/callback"
    return "https://dailyforge-backend-kwti.onrender.com/auth/github/callback"


@router.post("/github/start")
def github_start(request: Request, response: Response):
    """Initiate GitHub OAuth flow. Returns the authorization URL."""
    state = generate_oauth_state()
    _oauth_states[state] = datetime.now(timezone.utc).timestamp()

    # Clean up stale states (>10 min)
    cutoff = datetime.now(timezone.utc).timestamp() - 600
    expired = [k for k, v in _oauth_states.items() if v < cutoff]
    for k in expired:
        del _oauth_states[k]

    redirect_uri = get_redirect_uri(request)

    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user",
        "state": state,
    }
    url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return {"auth_url": url, "state": state}


@router.get("/github/callback")
def github_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Handle GitHub OAuth callback. Validates state, exchanges code, creates session."""
    frontend_target = settings.frontend_url or "https://geeky-rish.github.io/DailyForge"
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    if "localhost" in frontend_target and "onrender.com" in host:
        frontend_target = "https://geeky-rish.github.io/DailyForge"

    if error:
        logger.warning("OAuth error from GitHub: %s", error)
        return RedirectResponse(url=f"{frontend_target}?auth_error={error}")

    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code or state")

    # Validate state
    if state not in _oauth_states:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")
    del _oauth_states[state]

    redirect_uri = get_redirect_uri(request)

    # Exchange code for access token
    try:
        with httpx.Client(timeout=15) as client:
            token_resp = client.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            token_data = token_resp.json()
    except Exception as exc:
        logger.error("Token exchange failed: %s", exc)
        raise HTTPException(status_code=502, detail="GitHub token exchange failed")

    access_token = token_data.get("access_token")
    if not access_token:
        logger.warning("No access_token in GitHub response: %s", list(token_data.keys()))
        raise HTTPException(status_code=400, detail="GitHub did not return an access token")

    # Fetch GitHub user info
    try:
        with httpx.Client(timeout=15) as client:
            user_resp = client.get(
                GITHUB_USER_URL,
                headers={"Authorization": f"token {access_token}", "Accept": "application/json"},
            )
            gh_user = user_resp.json()
    except Exception as exc:
        logger.error("GitHub user fetch failed: %s", exc)
        raise HTTPException(status_code=502, detail="GitHub user fetch failed")

    gh_id = gh_user.get("id")
    gh_username = gh_user.get("login", "")

    # Authorization check: compare numeric GitHub user ID
    if settings.authorized_github_user_id and gh_id != settings.authorized_github_user_id:
        logger.warning("Unauthorized login attempt: github_id=%s username=%s", gh_id, gh_username)
        return RedirectResponse(url=f"{settings.frontend_url}?auth_error=unauthorized")

    # Also check username as belt-and-suspenders (primary check is user ID above)
    if gh_username.lower() != settings.authorized_github_username.lower():
        logger.warning("Username mismatch: expected %s got %s", settings.authorized_github_username, gh_username)
        return RedirectResponse(url=f"{settings.frontend_url}?auth_error=unauthorized")

    # Upsert user
    user = db.execute(select(User).where(User.github_id == gh_id)).scalar_one_or_none()
    if user:
        user.github_username = gh_username
        user.github_avatar_url = gh_user.get("avatar_url")
        user.github_name = gh_user.get("name")
        user.last_login = datetime.now(timezone.utc)
    else:
        user = User(
            github_id=gh_id,
            github_username=gh_username,
            github_avatar_url=gh_user.get("avatar_url"),
            github_name=gh_user.get("name"),
            last_login=datetime.now(timezone.utc),
        )
        db.add(user)
    db.commit()
    db.refresh(user)

    # Create session JWT
    jwt_token = create_access_token({"github_id": gh_id, "sub": gh_username})

    # Set HTTP-only cookie and redirect to frontend
    redirect_separator = "&" if "?" in frontend_target else "?"
    redirect_url = f"{frontend_target}{redirect_separator}auth=success&token={jwt_token}"
    response = RedirectResponse(url=redirect_url)
    is_prod = settings.app_env == "production"
    response.set_cookie(
        key="session_token",
        value=jwt_token,
        httponly=True,
        secure=is_prod,
        samesite="lax" if not is_prod else "none",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    logger.info("User %s (id=%s) logged in successfully", gh_username, gh_id)
    return response


@router.post("/logout")
def logout(response: Response):
    """Clear session cookie."""
    response.delete_cookie("session_token", path="/")
    return {"status": "logged_out"}
