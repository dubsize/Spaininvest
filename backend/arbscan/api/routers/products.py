from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arbscan.api.deps import DB, User
from arbscan.api.schemas import ListingSummary, ProductIn, ProductOut, ValuationOut
from arbscan.db.models import CanonicalProduct, Category, Listing, Opportunity, Valuation, Watchlist
from arbscan.fees.engine import TradeContext
from arbscan.normalization.catalog import normalizer_cache
from arbscan.normalization.engine import parse_variant_key
from arbscan.normalization.text import fold
from arbscan.services.pipeline import Evaluator, category_costs, evaluate_all, normalize_listing

router = APIRouter(prefix="/products", tags=["products"])


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", fold(text)).strip("-")[:110]


@router.get("")
def list_products(db: Session = DB, user: str = User, q: str | None = None, category: str | None = None) -> list[dict]:
    stmt = select(CanonicalProduct)
    if q:
        stmt = stmt.where(func.lower(CanonicalProduct.name).like(f"%{q.lower()}%"))
    if category:
        stmt = stmt.where(CanonicalProduct.category_code == category)
    products = db.scalars(stmt.order_by(CanonicalProduct.category_code, CanonicalProduct.name)).unique().all()
    counts = dict(
        db.execute(
            select(Listing.canonical_product_id, func.count()).where(Listing.status == "active").group_by(Listing.canonical_product_id)
        ).all()
    )
    opp_counts = dict(
        db.execute(
            select(Opportunity.canonical_product_id, func.count())
            .where(Opportunity.is_active.is_(True)).group_by(Opportunity.canonical_product_id)
        ).all()
    )
    # latest overall valuation per product (variant "" , first resale market)
    latest: dict[int, Valuation] = {}
    for v in db.scalars(select(Valuation).where(Valuation.variant_key == "").order_by(Valuation.computed_at)):
        latest[v.canonical_product_id] = v
    out = []
    for p in products:
        v = latest.get(p.id)
        out.append({
            **ProductOut.model_validate(p).model_dump(mode="json"),
            "active_listings": counts.get(p.id, 0),
            "active_opportunities": opp_counts.get(p.id, 0),
            "market_value_eur": v.market_value_eur if v else None,
            "quick_sale_eur": v.quick_sale_eur if v else None,
            "confidence_level": v.confidence_level if v else None,
            "n_comparables": v.n_comparables if v else 0,
        })
    return out


@router.post("", status_code=201)
def create_product(body: ProductIn, db: Session = DB, user: str = User) -> dict:
    if not db.get(Category, body.category_code):
        raise HTTPException(400, f"unknown category '{body.category_code}'")
    slug = body.slug or _slugify(f"{body.brand} {body.model}")
    if db.scalars(select(CanonicalProduct).where(CanonicalProduct.slug == slug)).first():
        raise HTTPException(409, f"slug '{slug}' already exists")
    p = CanonicalProduct(**{**body.model_dump(), "slug": slug})
    db.add(p)
    db.flush()
    normalizer_cache.invalidate()
    return ProductOut.model_validate(p).model_dump(mode="json")


def _get(db: Session, pid: int) -> CanonicalProduct:
    p = db.get(CanonicalProduct, pid)
    if not p:
        raise HTTPException(404, "product not found")
    return p


@router.put("/{pid}")
def update_product(pid: int, body: ProductIn, db: Session = DB, user: str = User) -> dict:
    p = _get(db, pid)
    for k, v in body.model_dump(exclude={"slug"}).items():
        setattr(p, k, v)
    db.flush()
    normalizer_cache.invalidate()
    return ProductOut.model_validate(p).model_dump(mode="json")


@router.delete("/{pid}")
def delete_product(pid: int, db: Session = DB, user: str = User) -> dict:
    p = _get(db, pid)
    for l in db.scalars(select(Listing).where(Listing.canonical_product_id == pid)):
        l.canonical_product_id = None
        l.normalization_confidence = 0.0
    for w in db.scalars(select(Watchlist).where(Watchlist.canonical_product_id == pid)):
        w.canonical_product_id = None
    for o in db.scalars(select(Opportunity).where(Opportunity.canonical_product_id == pid)):
        o.is_active = False
        o.canonical_product_id = None
    db.delete(p)
    db.flush()
    normalizer_cache.invalidate()
    return {"ok": True}


@router.post("/{pid}/renormalize")
def renormalize(pid: int, db: Session = DB, user: str = User) -> dict:
    """Re-run normalisation over all listings (after editing aliases/patterns) and re-score."""
    _get(db, pid)
    normalizer_cache.invalidate()
    norm = normalizer_cache.get(db)
    n = 0
    for l in db.scalars(select(Listing).where(Listing.status == "active")):
        before = l.canonical_product_id
        normalize_listing(l, norm)
        n += int(before != l.canonical_product_id)
    db.flush()
    evaluate_all(db)
    return {"relinked": n}


@router.get("/{pid}")
def product_detail(pid: int, db: Session = DB, user: str = User, market: str = "ES") -> dict:
    p = _get(db, pid)
    now = datetime.now(UTC)
    ev = Evaluator(db)
    cat = ev.categories[p.category_code]

    vals = db.scalars(
        select(Valuation).where(Valuation.canonical_product_id == pid, Valuation.market == market).order_by(Valuation.computed_at)
    ).all()
    latest_by_variant: dict[str, Valuation] = {}
    history: dict[str, list[dict]] = {}
    for v in vals:
        latest_by_variant[v.variant_key] = v
        history.setdefault(v.variant_key, []).append({
            "t": v.computed_at.isoformat(), "market_value": v.market_value_eur, "quick_sale": v.quick_sale_eur,
            "p25": v.p25_eur, "p75": v.p75_eur, "n": v.n_comparables,
        })

    # live valuation (overall) + max buy price per variant for a domestic purchase
    target_roi, _ = ev.target_rois(p)
    variants = []
    for key, v in sorted(latest_by_variant.items(), key=lambda kv: -(kv[1].n_comparables)):
        live = ev.valuation_for(p, market, attrs=parse_variant_key(key))
        max_buy = None
        if live.quick_sale_eur:
            ctx = TradeContext(
                source_marketplace="wallapop" if market == "ES" else "manual", source_country=market,
                resale_marketplace=ev.resale_marketplace(cat.code, market), resale_country=market,
                category=category_costs(cat), refurbishment_override_eur=p.refurbishment_eur,
            )
            max_buy = ev.fee_engine.max_buy_price(live.quick_sale_eur, ctx, target_roi=target_roi, min_profit_eur=float(ev.business.get("min_profit_eur", 0)))
        hist = history.get(key, [])
        trend = None
        month_ago = [h for h in hist if datetime.fromisoformat(h["t"]) <= now - timedelta(days=25)]
        if month_ago and month_ago[-1]["market_value"] and live.market_value_eur:
            trend = round(live.market_value_eur / month_ago[-1]["market_value"] - 1, 4)
        variants.append({
            "variant_key": key,
            "attributes": parse_variant_key(key),
            "valuation": live.as_dict(),
            "latest_snapshot": ValuationOut.model_validate(v).model_dump(mode="json"),
            "max_buy_price_eur": max_buy,
            "target_roi": target_roi,
            "trend_30d": trend,
            "history": hist,
        })

    listings = db.scalars(select(Listing).where(Listing.canonical_product_id == pid).order_by(Listing.first_seen_at.desc())).unique().all()
    active = [l for l in listings if l.status == "active"]
    prices = sorted(float(l.price_eur) for l in active)
    histogram = []
    if prices:
        lo, hi = prices[0], prices[-1]
        nb = min(14, max(4, len(prices) // 2))
        width = max(1.0, (hi - lo) / nb)
        for i in range(nb):
            a, b = lo + i * width, lo + (i + 1) * width
            histogram.append({"from": round(a), "to": round(b), "count": sum(1 for x in prices if a <= x < b or (i == nb - 1 and x == b))})
    by_mp: dict[str, list[float]] = {}
    for l in active:
        by_mp.setdefault(f"{l.marketplace_code}|{l.country}", []).append(float(l.price_eur))
    comparisons = []
    for k, vs in sorted(by_mp.items()):
        vs.sort()
        mp, country = k.split("|")
        comparisons.append({"marketplace": mp, "country": country, "n": len(vs), "median": vs[len(vs) // 2], "min": vs[0], "max": vs[-1]})

    return {
        "product": ProductOut.model_validate(p).model_dump(mode="json"),
        "category": {"code": cat.code, "name": cat.name, "is_luxury": cat.is_luxury, "target_roi": cat.target_roi},
        "market": market,
        "variants": variants,
        "price_distribution": histogram,
        "marketplace_comparison": comparisons,
        "active_listings": [ListingSummary.model_validate(l).model_dump(mode="json") for l in active[:100]],
        "recent_listings": [ListingSummary.model_validate(l).model_dump(mode="json") for l in listings[:25]],
        "counts": {"active": len(active), "total": len(listings), "ended": sum(1 for l in listings if l.status != "active")},
    }


class NormalizeIn(BaseModel):
    title: str = Field(max_length=500)
    description: str = Field(default="", max_length=20000)
    brand: str | None = None


@router.post("/normalize/test")
def test_normalization(body: NormalizeIn, db: Session = DB, user: str = User) -> dict:
    norm = normalizer_cache.get(db)
    res = norm.normalize(body.title, body.description, brand_hint=body.brand)
    return {**res.as_dict(), "product_name": res.product_name, "authenticity_info": res.authenticity_info}
