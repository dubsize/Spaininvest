from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from arbscan.api.deps import DB, User
from arbscan.api.schemas import DealIn, DealOut, DealPatch, SaleIn, StatusIn
from arbscan.db.models import Deal, StatusEvent
from arbscan.services.deals import (
    TransitionError,
    deal_metrics,
    log_status,
    portfolio_summary,
    set_deal_status,
)

router = APIRouter(tags=["deals"])


def _out(d: Deal) -> dict:
    out = DealOut.model_validate(d).model_dump(mode="json")
    out["metrics"] = deal_metrics(d).__dict__
    return out


@router.get("/deals")
def list_deals(db: Session = DB, user: str = User, status: str | None = None) -> list[dict]:
    stmt = select(Deal).order_by(Deal.purchase_date.desc().nulls_last(), Deal.id.desc())
    if status:
        stmt = stmt.where(Deal.status == status)
    return [_out(d) for d in db.scalars(stmt)]


@router.post("/deals", status_code=201)
def create_deal(body: DealIn, db: Session = DB, user: str = User) -> dict:
    """Record a purchase that did not come from a scanned opportunity."""
    d = Deal(status="PURCHASED", **body.model_dump())
    db.add(d)
    db.flush()
    log_status(db, "deal", d.id, None, "PURCHASED", "manual deal")
    return _out(d)


def _get(db: Session, did: int) -> Deal:
    d = db.get(Deal, did)
    if not d:
        raise HTTPException(404, "deal not found")
    return d


@router.get("/deals/{did}")
def get_deal(did: int, db: Session = DB, user: str = User) -> dict:
    d = _get(db, did)
    events = db.scalars(select(StatusEvent).where(StatusEvent.entity == "deal", StatusEvent.entity_id == did).order_by(StatusEvent.created_at)).all()
    return {**_out(d), "events": [{"from": e.from_status, "to": e.to_status, "note": e.note, "at": e.created_at.isoformat()} for e in events]}


@router.patch("/deals/{did}")
def patch_deal(did: int, body: DealPatch, db: Session = DB, user: str = User) -> dict:
    d = _get(db, did)
    data = body.model_dump(exclude_unset=True)
    status = data.pop("status", None)
    for k, v in data.items():
        setattr(d, k, v)
    if status:
        try:
            set_deal_status(db, d, status, data)
        except (TransitionError, ValueError) as exc:
            raise HTTPException(400, str(exc)) from exc
    db.flush()
    return _out(d)


@router.post("/deals/{did}/status")
def deal_status(did: int, body: StatusIn, db: Session = DB, user: str = User) -> dict:
    d = _get(db, did)
    try:
        set_deal_status(db, d, body.status, {"note": body.note})
    except (TransitionError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return _out(d)


@router.post("/deals/{did}/sell")
def sell(did: int, body: SaleIn, db: Session = DB, user: str = User) -> dict:
    d = _get(db, did)
    try:
        set_deal_status(db, d, "SOLD", body.model_dump())
    except (TransitionError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    db.flush()
    return _out(d)


@router.delete("/deals/{did}")
def delete_deal(did: int, db: Session = DB, user: str = User) -> dict:
    db.delete(_get(db, did))
    return {"ok": True}


@router.get("/portfolio")
def portfolio(db: Session = DB, user: str = User) -> dict:
    return portfolio_summary(db)
