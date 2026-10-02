"""Single-user authentication, sessions, CSRF and rate limiting.

* Password: bcrypt hash in ``ADMIN_PASSWORD_HASH`` (preferred) or plaintext
  ``ADMIN_PASSWORD`` (dev only - a warning is logged).
* Session: signed JWT in an ``HttpOnly; SameSite=Lax`` cookie (``Secure`` in production).
* CSRF: double-submit token. A non-HttpOnly ``arbscan_csrf`` cookie is issued at login;
  every state-changing request must echo it in the ``X-CSRF-Token`` header.
"""

from __future__ import annotations

import hmac
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response, status

from arbscan.core.config import Settings, get_settings
from arbscan.core.logging import get_logger

log = get_logger(__name__)

SESSION_COOKIE = "arbscan_session"
CSRF_COOKIE = "arbscan_csrf"
CSRF_HEADER = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    if s.admin_password_hash:
        try:
            return bcrypt.checkpw(password.encode(), s.admin_password_hash.encode())
        except ValueError:
            return False
    if s.admin_password:
        if s.environment == "production":
            log.warning("ADMIN_PASSWORD (plaintext) used in production - set ADMIN_PASSWORD_HASH instead")
        return hmac.compare_digest(password.encode(), s.admin_password.encode())
    return False


def create_session_token(username: str, settings: Settings | None = None) -> str:
    s = settings or get_settings()
    now = datetime.now(UTC)
    payload = {"sub": username, "iat": int(now.timestamp()), "exp": int((now + timedelta(hours=s.session_hours)).timestamp())}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_session_token(token: str, settings: Settings | None = None) -> str | None:
    s = settings or get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return sub if sub == s.admin_username else None


def set_session_cookies(response: Response, username: str) -> str:
    s = get_settings()
    token = create_session_token(username)
    csrf = secrets.token_urlsafe(32)
    max_age = s.session_hours * 3600
    response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=s.cookie_secure, samesite="lax", max_age=max_age, path="/")
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, secure=s.cookie_secure, samesite="lax", max_age=max_age, path="/")
    return csrf


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


def current_user(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:]
    user = decode_session_token(token) if token else None
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    # CSRF only matters for cookie-authenticated, state-changing requests
    if request.method not in SAFE_METHODS and request.cookies.get(SESSION_COOKIE):
        cookie = request.cookies.get(CSRF_COOKIE, "")
        header = request.headers.get(CSRF_HEADER, "")
        if not cookie or not hmac.compare_digest(cookie, header):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF token missing or invalid")
    return user


class SlidingWindowLimiter:
    """Per-key in-memory limiter (single API process is enough for a single user)."""

    def __init__(self) -> None:
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str, limit: int, window: float = 60.0) -> bool:
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True


limiter = SlidingWindowLimiter()
