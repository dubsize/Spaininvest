"""FastAPI application factory."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from arbscan.api.routers import (
    alerts,
    auth,
    config,
    dashboard,
    deals,
    io,
    listings,
    opportunities,
    products,
    scanner,
    watchlists,
)
from arbscan.api.security import limiter
from arbscan.core.config import get_settings
from arbscan.core.logging import configure_logging, get_logger
from arbscan.db.session import SessionLocal

log = get_logger("arbscan.api")


def create_app() -> FastAPI:
    s = get_settings()
    configure_logging(s.log_level, s.log_json)
    if s.jwt_secret in ("", "change-me-in-.env") and s.environment == "production":
        raise RuntimeError("JWT_SECRET must be set in production")
    if not (s.admin_password or s.admin_password_hash):
        log.warning("no ADMIN_PASSWORD / ADMIN_PASSWORD_HASH configured - login is impossible")

    app = FastAPI(
        title="ArbScan API",
        version="0.2.0",
        description="Second-hand deal & arbitrage scanner",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-CSRF-Token", "Authorization"],
    )

    @app.middleware("http")
    async def security_and_logging(request: Request, call_next):  # noqa: ANN001
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        ip = request.client.host if request.client else "?"
        if request.url.path.startswith("/api/") and not limiter.allow(f"api:{ip}", s.api_rate_limit_per_minute):
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.exception("unhandled error", extra={"path": request.url.path, "request_id": rid})
            response = JSONResponse({"detail": "internal error", "request_id": rid}, status_code=500)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'" if not request.url.path.startswith("/api/docs") else response.headers.get("Content-Security-Policy", "")
        if request.url.path != "/api/health":
            log.info(
                "request",
                extra={"method": request.method, "path": request.url.path, "status": response.status_code,
                       "ms": round((time.perf_counter() - t0) * 1000, 1), "request_id": rid},
            )
        return response

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        db_ok = True
        try:
            with SessionLocal() as session:
                session.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001
            db_ok = False
        return {"status": "ok" if db_ok else "degraded", "database": db_ok, "version": app.version}

    for r in (auth, dashboard, opportunities, listings, products, watchlists, scanner, deals, alerts, config, io):
        app.include_router(r.router, prefix="/api")
    return app


app = create_app()
