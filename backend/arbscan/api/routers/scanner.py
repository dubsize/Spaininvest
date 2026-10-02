from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from arbscan.api.deps import DB, User
from arbscan.api.schemas import MarketplaceOut, MarketplaceUpdate, ScanRunOut
from arbscan.connectors.registry import CONNECTORS, build_connector
from arbscan.db.models import Marketplace, ScanRun

router = APIRouter(prefix="/scanner", tags=["scanner"])


@router.get("/marketplaces")
def marketplaces(db: Session = DB, user: str = User) -> list[dict]:
    now = datetime.now(UTC)
    out = []
    stats = {
        code: (n, errs, new, dur)
        for code, n, errs, new, dur in db.execute(
            select(
                ScanRun.marketplace_code, func.count(), func.sum(case((ScanRun.status == "error", 1), else_=0)),
                func.sum(ScanRun.listings_new), func.avg(ScanRun.duration_ms),
            ).where(ScanRun.started_at >= now - timedelta(hours=24)).group_by(ScanRun.marketplace_code)
        ).all()
    }
    for m in db.scalars(select(Marketplace).order_by(Marketplace.enabled.desc(), Marketplace.code)):
        cls = CONNECTORS.get(m.connector_key)
        connector = build_connector(m.connector_key, m.code, m.config) if cls else None
        n, errs, new, dur = stats.get(m.code, (0, 0, 0, None))
        out.append({
            **MarketplaceOut.model_validate(m).model_dump(mode="json"),
            "connector_name": cls.display_name if cls else m.connector_key,
            "compliance_method": cls.compliance.method if cls else None,
            "compliance_docs": cls.compliance.docs_url if cls else None,
            "configured": connector.is_configured() if connector else False,
            "is_stub": connector.is_stub if connector else True,
            "scans_24h": n or 0,
            "errors_24h": int(errs or 0),
            "new_listings_24h": int(new or 0),
            "avg_duration_ms": round(dur) if dur else None,
        })
    return out


@router.patch("/marketplaces/{code}")
def update_marketplace(code: str, body: MarketplaceUpdate, db: Session = DB, user: str = User) -> dict:
    m = db.get(Marketplace, code)
    if not m:
        raise HTTPException(404, "marketplace not found")
    data = body.model_dump(exclude_unset=True)
    if data.get("enabled"):
        connector = build_connector(m.connector_key, m.code, m.config)
        if connector.is_stub:
            raise HTTPException(400, f"{m.name} has no compliant automated connector - use manual entry / CSV import")
    for k, v in data.items():
        if k == "config" and v is not None:
            m.config = {**(m.config or {}), **v}
        else:
            setattr(m, k, v)
    m.next_run_at = None
    db.flush()
    return MarketplaceOut.model_validate(m).model_dump(mode="json")


@router.post("/marketplaces/{code}/health")
def health(code: str, db: Session = DB, user: str = User) -> dict:
    m = db.get(Marketplace, code)
    if not m:
        raise HTTPException(404, "marketplace not found")
    h = build_connector(m.connector_key, m.code, m.config).health_check()
    return h.__dict__


@router.post("/marketplaces/{code}/run")
def run_now(code: str, db: Session = DB, user: str = User) -> dict:
    """Queue a scan (Celery) - falls back to running inline if the queue is unavailable."""
    m = db.get(Marketplace, code)
    if not m:
        raise HTTPException(404, "marketplace not found")
    try:
        import redis

        from arbscan.core.config import get_settings

        redis.Redis.from_url(get_settings().redis_url, socket_connect_timeout=1, socket_timeout=1).ping()
        from arbscan.workers.tasks import scan_marketplace

        r = scan_marketplace.apply_async(args=[code], kwargs={"force": True}, expires=600)
        return {"queued": True, "task_id": r.id}
    except Exception:  # noqa: BLE001 - broker down: run inline (small scans only)
        from arbscan.services.scanner import run_marketplace_scan

        run = run_marketplace_scan(db, code, force=True)
        return {"queued": False, "run": ScanRunOut.model_validate(run).model_dump(mode="json")}


@router.get("/runs")
def runs(db: Session = DB, user: str = User, marketplace: str | None = None, limit: int = 100) -> list[dict]:
    stmt = select(ScanRun).order_by(ScanRun.started_at.desc()).limit(min(limit, 500))
    if marketplace:
        stmt = stmt.where(ScanRun.marketplace_code == marketplace)
    return [ScanRunOut.model_validate(r).model_dump(mode="json") for r in db.scalars(stmt)]
