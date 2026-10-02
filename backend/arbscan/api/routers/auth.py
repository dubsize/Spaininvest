from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from arbscan.api.deps import User
from arbscan.api.schemas import LoginIn
from arbscan.api.security import clear_session_cookies, limiter, set_session_cookies, verify_password
from arbscan.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response) -> dict:
    s = get_settings()
    ip = request.client.host if request.client else "?"
    if not limiter.allow(f"login:{ip}", s.login_rate_limit_per_minute):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too many login attempts, wait a minute")
    if body.username != s.admin_username or not verify_password(body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    csrf = set_session_cookies(response, body.username)
    return {"username": body.username, "csrf_token": csrf}


@router.post("/logout")
def logout(response: Response, user: str = User) -> dict:
    clear_session_cookies(response)
    return {"ok": True}


@router.get("/me")
def me(user: str = User) -> dict:
    return {"username": user}
