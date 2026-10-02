"""Settings: categories, fee rules, cost profiles, business/scoring/valuation/scanner settings."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from arbscan.api.deps import DB, User
from arbscan.api.schemas import CategoryIO, CostProfileIO, FeeRuleIO
from arbscan.db.models import Category, CostProfile, FeeRule
from arbscan.seed.loader import purge_demo_data
from arbscan.services.pipeline import evaluate_all, snapshot_all_valuations
from arbscan.services.settings_service import DEFAULTS, get_setting, set_setting

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/app")
def app_settings(db: Session = DB, user: str = User) -> dict:
    return {k: get_setting(db, k) for k in DEFAULTS}


@router.put("/app/{key}")
def update_app_setting(key: str, body: dict[str, Any], db: Session = DB, user: str = User) -> dict:
    if key not in DEFAULTS:
        raise HTTPException(404, "unknown settings group")
    allowed = set(DEFAULTS[key]())
    unknown = set(body) - allowed
    if unknown:
        raise HTTPException(400, f"unknown keys: {sorted(unknown)}")
    return set_setting(db, key, body)


@router.post("/recompute")
def recompute(db: Session = DB, user: str = User) -> dict:
    """Re-run valuations and scoring with the current settings."""
    n_val = snapshot_all_valuations(db)
    n = evaluate_all(db)
    return {"valuations": n_val, "listings_evaluated": n}


@router.post("/purge-demo")
def purge_demo(db: Session = DB, user: str = User) -> dict:
    return {"deleted_listings": purge_demo_data(db)}


# ---------------------------------------------------------------------------- categories
@router.get("/categories")
def categories(db: Session = DB, user: str = User) -> list[dict]:
    return [CategoryIO.model_validate(c).model_dump() for c in db.scalars(select(Category).order_by(Category.code))]


@router.put("/categories/{code}")
def upsert_category(code: str, body: CategoryIO, db: Session = DB, user: str = User) -> dict:
    c = db.get(Category, code)
    if c is None:
        c = Category(code=code)
        db.add(c)
    for k, v in body.model_dump(exclude={"code"}).items():
        setattr(c, k, v)
    db.flush()
    return CategoryIO.model_validate(c).model_dump()


# ---------------------------------------------------------------------------- fee rules
@router.get("/fees")
def fees(db: Session = DB, user: str = User) -> list[dict]:
    return [FeeRuleIO.model_validate(f).model_dump() for f in db.scalars(select(FeeRule).order_by(FeeRule.side, FeeRule.marketplace_code))]


@router.post("/fees", status_code=201)
def create_fee(body: FeeRuleIO, db: Session = DB, user: str = User) -> dict:
    f = FeeRule(**body.model_dump(exclude={"id"}))
    db.add(f)
    db.flush()
    return FeeRuleIO.model_validate(f).model_dump()


@router.put("/fees/{fid}")
def update_fee(fid: int, body: FeeRuleIO, db: Session = DB, user: str = User) -> dict:
    f = db.get(FeeRule, fid)
    if not f:
        raise HTTPException(404, "fee rule not found")
    for k, v in body.model_dump(exclude={"id"}).items():
        setattr(f, k, v)
    db.flush()
    return FeeRuleIO.model_validate(f).model_dump()


@router.delete("/fees/{fid}")
def delete_fee(fid: int, db: Session = DB, user: str = User) -> dict:
    f = db.get(FeeRule, fid)
    if not f:
        raise HTTPException(404, "fee rule not found")
    db.delete(f)
    return {"ok": True}


# ---------------------------------------------------------------------------- cost profiles
@router.get("/costs")
def costs(db: Session = DB, user: str = User) -> list[dict]:
    return [CostProfileIO.model_validate(c).model_dump() for c in db.scalars(select(CostProfile).order_by(CostProfile.route, CostProfile.name))]


@router.post("/costs", status_code=201)
def create_cost(body: CostProfileIO, db: Session = DB, user: str = User) -> dict:
    c = CostProfile(**body.model_dump(exclude={"id"}))
    db.add(c)
    db.flush()
    return CostProfileIO.model_validate(c).model_dump()


@router.put("/costs/{cid}")
def update_cost(cid: int, body: CostProfileIO, db: Session = DB, user: str = User) -> dict:
    c = db.get(CostProfile, cid)
    if not c:
        raise HTTPException(404, "cost profile not found")
    for k, v in body.model_dump(exclude={"id"}).items():
        setattr(c, k, v)
    db.flush()
    return CostProfileIO.model_validate(c).model_dump()


@router.delete("/costs/{cid}")
def delete_cost(cid: int, db: Session = DB, user: str = User) -> dict:
    c = db.get(CostProfile, cid)
    if not c:
        raise HTTPException(404, "cost profile not found")
    db.delete(c)
    return {"ok": True}
