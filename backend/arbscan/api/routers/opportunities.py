from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from arbscan.api.deps import DB, User
from arbscan.api.schemas import OfferIn, OpportunityOut, PurchaseIn, StatusIn
from arbscan.db.models import CanonicalProduct, Listing, Opportunity
from arbscan.scoring.offer import OfferInput, calculate_offer
from arbscan.services.deals import TransitionError, purchase_opportunity, set_opportunity_status
from arbscan.services.pipeline import Evaluator

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

SORTABLE = {
    "score": Opportunity.score,
    "net_profit": Opportunity.net_profit_quick_eur,
    "roi": Opportunity.roi,
    "discount": Opportunity.discount_pct,
    "price": Opportunity.purchase_price_eur,
    "market_value": Opportunity.market_value_eur,
    "quick_sale": Opportunity.quick_sale_eur,
    "liquidity": Opportunity.liquidity_score,
    "risk": Opportunity.risk_score,
    "annualized_roi": Opportunity.annualized_roi,
    "profit_velocity": Opportunity.profit_velocity,
    "confidence": Opportunity.confidence_score,
    "first_seen": Listing.first_seen_at,
    "published": Listing.published_at,
    "age": Listing.published_at,
    "price_drop": Listing.last_price_change_at,
    "country": Listing.country,
    "marketplace": Listing.marketplace_code,
}


def filtered_query(
    *,
    q: str | None = None,
    marketplace: list[str] | None = None,
    country: list[str] | None = None,
    city: str | None = None,
    brand: list[str] | None = None,
    product_id: list[int] | None = None,
    category: list[str] | None = None,
    opportunity_type: list[str] | None = None,
    status: list[str] | None = None,
    risk: list[str] | None = None,
    condition: list[str] | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_discount: float | None = None,
    min_profit: float | None = None,
    min_roi: float | None = None,
    min_score: float | None = None,
    max_age_hours: float | None = None,
    min_seller_rating: float | None = None,
    resale_country: str | None = None,
    include_inactive: bool = False,
    include_demo: bool = True,
    price_dropped: bool | None = None,
) -> Select:
    stmt = select(Opportunity).join(Listing, Listing.id == Opportunity.listing_id).outerjoin(
        CanonicalProduct, CanonicalProduct.id == Opportunity.canonical_product_id
    )
    conds: list[Any] = []
    if not include_inactive:
        conds.append(Opportunity.is_active.is_(True))
    if not include_demo:
        conds.append(Listing.is_demo.is_(False))
    if q:
        like = f"%{q.lower()}%"
        conds.append(or_(func.lower(Listing.title).like(like), func.lower(CanonicalProduct.name).like(like)))
    if marketplace:
        conds.append(Listing.marketplace_code.in_(marketplace))
    if country:
        conds.append(Listing.country.in_([c.upper() for c in country]))
    if city:
        conds.append(func.lower(Listing.city).like(f"%{city.lower()}%"))
    if brand:
        conds.append(CanonicalProduct.brand.in_(brand))
    if product_id:
        conds.append(Opportunity.canonical_product_id.in_(product_id))
    if category:
        conds.append(CanonicalProduct.category_code.in_(category))
    if opportunity_type:
        conds.append(Opportunity.opportunity_type.in_(opportunity_type))
    if status:
        conds.append(Opportunity.status.in_(status))
    if risk:
        conds.append(Opportunity.risk_level.in_(risk))
    if condition:
        conds.append(Listing.condition.in_(condition))
    if min_price is not None:
        conds.append(Opportunity.purchase_price_eur >= min_price)
    if max_price is not None:
        conds.append(Opportunity.purchase_price_eur <= max_price)
    if min_discount is not None:
        conds.append(Opportunity.discount_pct >= min_discount)
    if min_profit is not None:
        conds.append(
            or_(
                Opportunity.net_profit_quick_eur >= min_profit,
                and_(Opportunity.opportunity_type == "NEGOTIATION", Opportunity.profit_at_target_offer_eur >= min_profit),
            )
        )
    if min_roi is not None:
        conds.append(Opportunity.roi >= min_roi)
    if min_score is not None:
        conds.append(Opportunity.score >= min_score)
    if max_age_hours is not None:
        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        conds.append(func.coalesce(Listing.published_at, Listing.first_seen_at) >= cutoff)
    if min_seller_rating is not None:
        conds.append(Listing.seller_rating >= min_seller_rating)
    if resale_country:
        conds.append(Opportunity.resale_country == resale_country.upper())
    if price_dropped:
        conds.append(Listing.price_drop_count > 0)
    return stmt.where(*conds) if conds else stmt


@router.get("")
def list_opportunities(
    db: Session = DB,
    user: str = User,
    q: str | None = None,
    marketplace: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    city: str | None = None,
    brand: list[str] | None = Query(None),
    product_id: list[int] | None = Query(None),
    category: list[str] | None = Query(None),
    type: list[str] | None = Query(None),
    status: list[str] | None = Query(None),
    risk: list[str] | None = Query(None),
    condition: list[str] | None = Query(None),
    min_price: float | None = None,
    max_price: float | None = None,
    min_discount: float | None = None,
    min_profit: float | None = None,
    min_roi: float | None = None,
    min_score: float | None = None,
    max_age_hours: float | None = None,
    min_seller_rating: float | None = None,
    resale_country: str | None = None,
    include_inactive: bool = False,
    include_demo: bool = True,
    price_dropped: bool | None = None,
    sort: str = "score",
    order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> dict:
    stmt = filtered_query(
        q=q, marketplace=marketplace, country=country, city=city, brand=brand, product_id=product_id,
        category=category, opportunity_type=type, status=status, risk=risk, condition=condition,
        min_price=min_price, max_price=max_price, min_discount=min_discount, min_profit=min_profit,
        min_roi=min_roi, min_score=min_score, max_age_hours=max_age_hours, min_seller_rating=min_seller_rating,
        resale_country=resale_country, include_inactive=include_inactive, include_demo=include_demo,
        price_dropped=price_dropped,
    )
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    col = SORTABLE.get(sort, Opportunity.score)
    ordering = col.asc() if order == "asc" else col.desc()
    rows = db.scalars(stmt.order_by(ordering.nulls_last(), Opportunity.id.desc()).offset((page - 1) * page_size).limit(page_size)).unique().all()
    return {
        "items": [OpportunityOut.model_validate(o).model_dump(mode="json") for o in rows],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }


@router.get("/facets")
def facets(db: Session = DB, user: str = User) -> dict:
    """Distinct filter values for the UI."""
    base = select(Listing).join(Opportunity, Opportunity.listing_id == Listing.id).where(Opportunity.is_active.is_(True))
    sub = base.subquery()
    return {
        "marketplaces": sorted({r for (r,) in db.execute(select(sub.c.marketplace_code).distinct())}),
        "countries": sorted({r for (r,) in db.execute(select(sub.c.country).distinct())}),
        "brands": sorted({r for (r,) in db.execute(select(CanonicalProduct.brand).distinct())}),
        "categories": sorted({r for (r,) in db.execute(select(CanonicalProduct.category_code).distinct())}),
        "conditions": ["new", "like_new", "very_good", "good", "fair", "for_parts", "unknown"],
        "types": ["FLIP", "CROSS_BORDER", "NEGOTIATION"],
        "risk": ["LOW", "MEDIUM", "HIGH"],
    }


def _get(db: Session, opp_id: int) -> Opportunity:
    opp = db.get(Opportunity, opp_id)
    if not opp:
        raise HTTPException(404, "opportunity not found")
    return opp


@router.get("/{opp_id}")
def get_opportunity(opp_id: int, db: Session = DB, user: str = User) -> dict:
    return OpportunityOut.model_validate(_get(db, opp_id)).model_dump(mode="json")


@router.post("/{opp_id}/status")
def change_status(opp_id: int, body: StatusIn, db: Session = DB, user: str = User) -> dict:
    opp = _get(db, opp_id)
    try:
        set_opportunity_status(db, opp, body.status, body.note)
    except (TransitionError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    db.flush()
    return OpportunityOut.model_validate(opp).model_dump(mode="json")


@router.post("/{opp_id}/purchase")
def purchase(opp_id: int, body: PurchaseIn, db: Session = DB, user: str = User) -> dict:
    opp = _get(db, opp_id)
    try:
        deal = purchase_opportunity(db, opp, body.model_dump())
    except (TransitionError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"deal_id": deal.id}


@router.post("/{opp_id}/offer")
def offer(opp_id: int, body: OfferIn, db: Session = DB, user: str = User) -> dict:
    """WHAT SHOULD I OFFER? - uses the fee engine unless explicit expected costs are given."""
    opp = _get(db, opp_id)
    ev = Evaluator(db)
    listing = opp.listing
    product = ev.products.get(opp.canonical_product_id) if opp.canonical_product_id else None
    expected_resale = body.expected_resale or opp.quick_sale_eur
    if not expected_resale:
        raise HTTPException(400, "no resale estimate available - provide expected_resale")
    target_roi = body.target_roi if body.target_roi is not None else (ev.target_rois(product)[0] if product else 0.25)
    ctx = ev.trade_context(listing, product, opp.resale_country) if product else None
    age = (opp.score_components or {}).get("listing_age_days", 0) or 0
    res = calculate_offer(
        OfferInput(
            asking_price=body.asking_price or opp.purchase_price_eur,
            expected_resale=expected_resale,
            target_roi=target_roi,
            target_profit_eur=body.target_profit_eur,
            expected_costs_eur=body.expected_costs_eur,
            listing_age_days=age,
            price_drops=listing.price_drop_count or 0,
        ),
        ev.fee_engine if ctx else None,
        ctx,
    )
    return {**res.__dict__, "target_roi": target_roi}


@router.post("/{opp_id}/recompute")
def recompute(opp_id: int, db: Session = DB, user: str = User) -> dict:
    opp = _get(db, opp_id)
    ev = Evaluator(db)
    ev.evaluate(opp.listing, opp.resale_country)
    db.flush()
    db.refresh(opp)
    return OpportunityOut.model_validate(opp).model_dump(mode="json")
