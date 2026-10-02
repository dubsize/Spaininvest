from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from arbscan.alerts.channels import AlertMessage, available_channels
from arbscan.api.deps import DB, User
from arbscan.api.schemas import AlertEventOut, AlertRuleIO
from arbscan.db.models import AlertEvent, AlertRule

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/rules")
def rules(db: Session = DB, user: str = User) -> list[dict]:
    return [AlertRuleIO.model_validate(r).model_dump() for r in db.scalars(select(AlertRule).order_by(AlertRule.id))]


@router.post("/rules", status_code=201)
def create_rule(body: AlertRuleIO, db: Session = DB, user: str = User) -> dict:
    r = AlertRule(**body.model_dump(exclude={"id"}))
    db.add(r)
    db.flush()
    return AlertRuleIO.model_validate(r).model_dump()


@router.put("/rules/{rid}")
def update_rule(rid: int, body: AlertRuleIO, db: Session = DB, user: str = User) -> dict:
    r = db.get(AlertRule, rid)
    if not r:
        raise HTTPException(404, "rule not found")
    for k, v in body.model_dump(exclude={"id"}).items():
        setattr(r, k, v)
    db.flush()
    return AlertRuleIO.model_validate(r).model_dump()


@router.delete("/rules/{rid}")
def delete_rule(rid: int, db: Session = DB, user: str = User) -> dict:
    r = db.get(AlertRule, rid)
    if not r:
        raise HTTPException(404, "rule not found")
    db.delete(r)
    return {"ok": True}


@router.get("/events")
def events(db: Session = DB, user: str = User, limit: int = 100) -> list[dict]:
    rows = db.scalars(select(AlertEvent).order_by(AlertEvent.created_at.desc()).limit(min(limit, 500)))
    return [AlertEventOut.model_validate(e).model_dump(mode="json") for e in rows]


@router.get("/channels")
def channels(user: str = User) -> list[dict]:
    return [{"name": n, "configured": c.is_configured()} for n, c in available_channels().items()]


@router.post("/channels/{name}/test")
def test_channel(name: str, user: str = User) -> dict:
    ch = available_channels().get(name)
    if not ch:
        raise HTTPException(404, "unknown channel")
    if not ch.is_configured():
        raise HTTPException(400, f"channel '{name}' is not configured (see .env.example)")
    try:
        ch.send(AlertMessage(subject="ArbScan test alert", text="✅ ArbScan test alert - your channel works."))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"send failed: {exc}") from exc
    return {"ok": True}
