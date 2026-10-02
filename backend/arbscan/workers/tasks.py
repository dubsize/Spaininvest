"""Background jobs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import redis
from sqlalchemy import select

from arbscan.core.config import get_settings
from arbscan.core.logging import configure_logging, get_logger
from arbscan.db.models import AppSetting, Listing
from arbscan.db.session import session_scope
from arbscan.services import scanner
from arbscan.services.pipeline import Evaluator, snapshot_all_valuations
from arbscan.services.settings_service import get_setting
from arbscan.workers.celery_app import celery_app

settings = get_settings()
configure_logging(settings.log_level, settings.log_json)
log = get_logger("arbscan.worker")


def _lock(name: str, ttl: int) -> bool:
    """Best-effort distributed lock so overlapping beats/workers never double-scan."""
    try:
        r = redis.Redis.from_url(settings.redis_url)
        return bool(r.set(f"lock:{name}", "1", nx=True, ex=ttl))
    except redis.RedisError:
        return True


def _unlock(name: str) -> None:
    try:
        redis.Redis.from_url(settings.redis_url).delete(f"lock:{name}")
    except redis.RedisError:
        pass


@celery_app.task(name="arbscan.tick")
def tick() -> list[str]:
    if not settings.scanner_enabled:
        return []
    with session_scope() as session:
        due = scanner.due_marketplaces(session)
    for code in due:
        scan_marketplace.apply_async(args=[code], expires=600)
    return due


@celery_app.task(name="arbscan.scan_marketplace")
def scan_marketplace(code: str, force: bool = False) -> dict:
    if not _lock(f"scan:{code}", 900):
        return {"skipped": "already running"}
    try:
        with session_scope() as session:
            run = scanner.run_marketplace_scan(session, code, force=force)
            return {"status": run.status, "new": run.listings_new, "opportunities": run.opportunities_created}
    finally:
        _unlock(f"scan:{code}")


def _due(session, key: str, minutes: float) -> bool:  # noqa: ANN001
    row = session.get(AppSetting, f"job:{key}")
    now = datetime.now(UTC)
    last = (row.value or {}).get("last") if row else None
    if last and datetime.fromisoformat(last) > now - timedelta(minutes=minutes):
        return False
    if row is None:
        session.add(AppSetting(key=f"job:{key}", value={"last": now.isoformat()}))
    else:
        row.value = {"last": now.isoformat()}
    return True


@celery_app.task(name="arbscan.analysis")
def analysis() -> dict:
    """Re-score active listings (freshness decays, new comparables arrive) and, on the
    slower cadence, append valuation snapshots for price history/trends."""
    if not _lock("analysis", 1800):
        return {"skipped": True}
    try:
        with session_scope() as session:
            cfg = get_setting(session, "scanner")
            n_val = snapshot_all_valuations(session) if _due(session, "valuations", cfg["analysis_minutes"]) else 0
            ev = Evaluator(session)
            n = 0
            for l in session.scalars(select(Listing).where(Listing.status == "active", Listing.canonical_product_id.is_not(None))):
                ev.evaluate(l)
                n += 1
            return {"rescored": n, "valuations": n_val}
    finally:
        _unlock("analysis")


@celery_app.task(name="arbscan.housekeeping")
def housekeeping() -> dict:
    with session_scope() as session:
        expired = scanner.expire_unseen_listings(session)
        fx = 0
        if settings.fx_auto_update:
            from arbscan.services.fx import update_from_ecb

            try:
                fx = update_from_ecb(session)
            except Exception as exc:  # noqa: BLE001
                log.warning("fx update failed", extra={"err": str(exc)})
        return {"expired": expired, "fx_rates": fx}
