from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from arbscan.api.deps import DB, User
from arbscan.api.schemas import ListingDetail, ListingPatch, ListingSummary, ManualListingIn, OpportunityOut
from arbscan.connectors.base import RawListing
from arbscan.connectors.page_metadata import detect_marketplace, external_id_from_url, fetch_metadata
from arbscan.db.models import Listing, ListingPriceHistory, Opportunity
from arbscan.normalization.ai import get_ai_normalizer
from arbscan.normalization.catalog import normalizer_cache
from arbscan.normalization.engine import make_variant_key
from arbscan.services.fx import FxService
from arbscan.services.pipeline import Evaluator, ingest_raw_listing, normalize_listing

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("")
def search_listings(
    db: Session = DB,
    user: str = User,
    q: str | None = None,
    product_id: int | None = None,
    marketplace: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    status: str | None = "active",
    unmatched: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict:
    stmt = select(Listing)
    if q:
        stmt = stmt.where(func.lower(Listing.title).like(f"%{q.lower()}%"))
    if product_id:
        stmt = stmt.where(Listing.canonical_product_id == product_id)
    if marketplace:
        stmt = stmt.where(Listing.marketplace_code.in_(marketplace))
    if country:
        stmt = stmt.where(Listing.country.in_(country))
    if status and status != "all":
        stmt = stmt.where(Listing.status == status)
    if unmatched:
        stmt = stmt.where(or_(Listing.canonical_product_id.is_(None), Listing.normalization_confidence < 0.5))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Listing.first_seen_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique().all()
    return {"items": [ListingSummary.model_validate(l).model_dump(mode="json") for l in rows], "total": total, "page": page, "page_size": page_size}


def _get(db: Session, listing_id: int) -> Listing:
    l = db.get(Listing, listing_id)
    if not l:
        raise HTTPException(404, "listing not found")
    return l


@router.get("/{listing_id}")
def get_listing(listing_id: int, db: Session = DB, user: str = User, include_raw: bool = False) -> dict:
    l = _get(db, listing_id)
    detail = ListingDetail.model_validate(l).model_dump(mode="json")
    if include_raw:
        detail["raw_payload"] = l.raw_payload
    opps = db.scalars(select(Opportunity).where(Opportunity.listing_id == l.id)).unique().all()
    product = l.canonical_product
    comparables = []
    if product is not None:
        ev = Evaluator(db)
        rows = ev.comparables(product.id)
        scored = []
        for row in rows:
            if row.listing_id == l.id:
                continue
            w = ev.valuation_engine.comparable_weight(
                row.comparable, target_attrs=dict(l.variant or {}), variant_importance=dict(product.variant_attributes or {}),
                market=opps[0].resale_country if opps else "ES", now=ev.now,
            )
            if w > 0:
                scored.append((w, row))
        scored.sort(key=lambda x: (-x[0], -(x[1].comparable.observed_at or ev.now).timestamp()))
        ids = [r.listing_id for _, r in scored[:40]]
        by_id = {x.id: x for x in db.scalars(select(Listing).where(Listing.id.in_(ids))).unique()}
        for w, r in scored[:40]:
            cl = by_id.get(r.listing_id)
            if cl is None:
                continue
            comparables.append({
                **ListingSummary.model_validate(cl).model_dump(mode="json"),
                "weight": round(w, 3),
                "kind": r.comparable.kind,
                "days_on_market": round(r.comparable.days_on_market, 1) if r.comparable.days_on_market is not None else None,
            })
    return {
        "listing": detail,
        "product": {"id": product.id, "name": product.name, "brand": product.brand, "category_code": product.category_code, "slug": product.slug} if product else None,
        "opportunities": [OpportunityOut.model_validate(o).model_dump(mode="json") for o in opps],
        "comparables": comparables,
    }


@router.patch("/{listing_id}")
def patch_listing(listing_id: int, body: ListingPatch, db: Session = DB, user: str = User) -> dict:
    l = _get(db, listing_id)
    data = body.model_dump(exclude_unset=True)
    fx = FxService(db)
    if "price" in data and data["price"] is not None and abs(data["price"] - l.price_amount) >= 0.01:
        eur, rate, _ = fx.to_eur(data["price"], l.currency)
        change = "drop" if data["price"] < l.price_amount else "increase"
        pct = (eur - l.price_eur) / l.price_eur if l.price_eur else None
        db.add(ListingPriceHistory(listing_id=l.id, price_amount=data["price"], currency=l.currency, price_eur=eur, fx_rate=rate, change_type=change, change_pct=pct))
        l.price_amount, l.price_eur = data["price"], eur
        l.last_price_change_at = datetime.now(UTC)
        l.last_price_change_pct = pct
        if change == "drop":
            l.price_drop_count += 1
    for f in ("title", "description", "city", "seller_rating", "seller_rating_count", "shipping_cost_eur", "status"):
        if f in data:
            setattr(l, f, data[f])
    if "country" in data and data["country"]:
        l.country = data["country"].upper()
    if "title" in data or "description" in data:
        normalize_listing(l, normalizer_cache.get(db))
    if "canonical_product_id" in data:
        l.canonical_product_id = data["canonical_product_id"]
        l.normalization_method = "manual"
        l.normalization_confidence = 1.0 if data["canonical_product_id"] else 0.0
    if "variant" in data and data["variant"] is not None:
        l.variant = data["variant"]
        l.normalization_method = "manual"
    if "condition" in data and data["condition"]:
        l.condition = data["condition"]
    if l.canonical_product is not None or l.canonical_product_id:
        db.flush()
        db.refresh(l)
        if l.canonical_product:
            l.variant_key = make_variant_key(dict(l.variant or {}), dict(l.canonical_product.variant_attributes or {}))
    db.flush()
    Evaluator(db).evaluate(l)
    db.flush()
    return get_listing(listing_id, db, user)


@router.post("/manual/prefill")
def manual_prefill(body: ManualListingIn, user: str = User) -> dict:
    """Detect the marketplace from the URL and (optionally) read public page metadata."""
    mp, country = detect_marketplace(body.url)
    md = fetch_metadata(body.url) if body.fetch_metadata else None
    return {
        "marketplace": mp,
        "country": country,
        "external_id": external_id_from_url(body.url),
        "metadata": md.__dict__ if md else None,
    }


@router.post("/manual")
def create_manual(body: ManualListingIn, db: Session = DB, user: str = User) -> dict:
    mp_detected, country_detected = detect_marketplace(body.url)
    title, price, description, images = body.title, body.price, body.description, list(body.image_urls)
    if body.fetch_metadata and (not title or not price):
        md = fetch_metadata(body.url)
        title = title or md.title
        price = price or md.price
        description = description or md.description or ""
        images = images or md.image_urls
    if not title or not price:
        raise HTTPException(400, "title and price are required (fill them manually if the page could not be read)")
    ext = external_id_from_url(body.url) if body.url else hashlib.sha1(f"{title}{price}".encode()).hexdigest()[:16]
    raw = RawListing(
        marketplace=body.marketplace or mp_detected,
        external_id=ext,
        url=body.url,
        title=title,
        price=float(price),
        currency=body.currency.upper(),
        country=(body.country or country_detected or "ES").upper(),
        city=body.city,
        description=description,
        condition_raw=body.condition,
        seller_name=body.seller_name,
        seller_rating=body.seller_rating,
        seller_rating_count=body.seller_rating_count,
        seller_account_created_at=body.seller_account_created_at,
        published_at=body.published_at,
        shipping_available=body.shipping_available,
        shipping_cost=body.shipping_cost,
        image_urls=images,
        price_kind="sold" if body.price_kind == "sold" else "asking",
        status="sold" if body.price_kind == "sold" else "active",
        sold_price=float(price) if body.price_kind == "sold" else None,
        source_metadata={"entered": "manual"},
    )
    res = ingest_raw_listing(db, raw, source="manual", ai=get_ai_normalizer())
    l = res.listing
    if body.condition:
        l.condition = body.condition if body.condition in {"new", "like_new", "very_good", "good", "fair", "for_parts"} else l.condition
    if body.canonical_product_id:
        l.canonical_product_id = body.canonical_product_id
        l.normalization_method = "manual"
        l.normalization_confidence = 1.0
    db.flush()
    Evaluator(db).evaluate(l)
    db.flush()
    return get_listing(l.id, db, user)


@router.delete("/{listing_id}")
def delete_listing(listing_id: int, db: Session = DB, user: str = User) -> dict:
    l = _get(db, listing_id)
    if l.source not in ("manual", "csv"):
        raise HTTPException(400, "only manual/CSV listings can be deleted (collected listings are kept for history)")
    db.delete(l)
    return {"ok": True}
