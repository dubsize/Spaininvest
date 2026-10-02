from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from arbscan.api.deps import DB, User
from arbscan.api.schemas import WatchlistIn, WatchlistOut
from arbscan.db.models import CanonicalProduct, Category, Watchlist

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


def _validate(db: Session, body: WatchlistIn) -> None:
    if body.canonical_product_id and not db.get(CanonicalProduct, body.canonical_product_id):
        raise HTTPException(400, "unknown product")
    if body.category_code and not db.get(Category, body.category_code):
        raise HTTPException(400, "unknown category")
    if not (body.keyword or body.canonical_product_id or body.category_code):
        raise HTTPException(400, "a keyword, product or category is required")


def _out(w: Watchlist) -> dict:
    return WatchlistOut.model_validate(w).model_dump(mode="json")


@router.get("")
def list_watchlists(db: Session = DB, user: str = User) -> list[dict]:
    return [_out(w) for w in db.scalars(select(Watchlist).order_by(Watchlist.priority, Watchlist.name)).unique()]


@router.post("", status_code=201)
def create_watchlist(body: WatchlistIn, db: Session = DB, user: str = User) -> dict:
    _validate(db, body)
    data = body.model_dump()
    data["countries"] = [c.upper() for c in data["countries"]]
    w = Watchlist(**data)
    db.add(w)
    db.flush()
    db.refresh(w)
    return _out(w)


@router.put("/{wid}")
def update_watchlist(wid: int, body: WatchlistIn, db: Session = DB, user: str = User) -> dict:
    w = db.get(Watchlist, wid)
    if not w:
        raise HTTPException(404, "watchlist not found")
    _validate(db, body)
    for k, v in body.model_dump().items():
        setattr(w, k, [c.upper() for c in v] if k == "countries" else v)
    w.next_scan_at = None  # rescan with new criteria
    db.flush()
    db.refresh(w)
    return _out(w)


@router.delete("/{wid}")
def delete_watchlist(wid: int, db: Session = DB, user: str = User) -> dict:
    w = db.get(Watchlist, wid)
    if not w:
        raise HTTPException(404, "watchlist not found")
    db.delete(w)
    return {"ok": True}


@router.get("/{wid}/matches")
def watchlist_matches(wid: int, db: Session = DB, user: str = User, limit: int = 100) -> dict:
    """Active opportunities that satisfy the watchlist's thresholds."""
    from arbscan.api.routers.opportunities import filtered_query
    from arbscan.api.schemas import OpportunityOut
    from arbscan.db.models import Opportunity

    w = db.get(Watchlist, wid)
    if not w:
        raise HTTPException(404, "watchlist not found")
    stmt = filtered_query(
        q=None if w.canonical_product_id else (w.keyword or None),
        product_id=[w.canonical_product_id] if w.canonical_product_id else None,
        category=[w.category_code] if w.category_code else None,
        brand=w.brands or None, country=w.countries or None, marketplace=w.marketplaces or None,
        max_price=w.max_price_eur, min_discount=w.min_discount, min_profit=w.min_profit_eur,
        min_roi=w.min_roi, min_score=w.min_score,
    )
    rows = db.scalars(stmt.order_by(Opportunity.score.desc()).limit(limit)).unique().all()
    return {"watchlist": _out(w), "items": [OpportunityOut.model_validate(o).model_dump(mode="json") for o in rows]}
