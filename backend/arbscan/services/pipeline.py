"""collection -> normalisation -> valuation -> scoring pipeline.

``ingest_raw_listing`` upserts what a connector (or manual entry / CSV / demo feed)
produced, keeping an append-only price history. ``Evaluator`` turns a listing into one
Opportunity per resale market using the marketplace-agnostic engines.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from arbscan.connectors.base import RawListing
from arbscan.core.logging import get_logger
from arbscan.db.enums import ListingSource, OpportunityType
from arbscan.db.models import (
    CanonicalProduct,
    Category,
    CostProfile,
    FeeRule,
    Listing,
    ListingPriceHistory,
    Marketplace,
    Opportunity,
    Valuation,
)
from arbscan.fees.engine import (
    CategoryCosts,
    CostProfileData,
    FeeEngine,
    FeeRuleData,
    TradeContext,
)
from arbscan.normalization.catalog import normalizer_cache
from arbscan.normalization.engine import NormalizationResult, RuleNormalizer, parse_variant_key
from arbscan.normalization.text import fold, sanitize_text
from arbscan.risk.engine import RiskEngine, RiskInput
from arbscan.scoring.engine import (
    LiquidityInput,
    ScoreInput,
    classify_opportunity,
    compute_score,
    estimate_liquidity,
    velocity_metrics,
)
from arbscan.services.fx import FxService
from arbscan.services.settings_service import get_setting, scoring_config, valuation_config
from arbscan.valuation.engine import Comparable, ValuationEngine, ValuationResult

log = get_logger(__name__)

MIN_MATCH_CONFIDENCE = 0.35
MIN_COMPARABLE_CONFIDENCE = 0.55


def utcnow() -> datetime:
    return datetime.now(UTC)


def aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


# ============================================================================ ingest


@dataclass
class IngestResult:
    listing: Listing
    created: bool
    updated: bool
    price_changed: bool
    price_change_pct: float | None = None


def apply_normalization(listing: Listing, result: NormalizationResult) -> None:
    if listing.normalization_method == "manual":
        return  # a human decision always wins
    listing.canonical_product_id = result.product_id if result.confidence >= MIN_MATCH_CONFIDENCE else None
    listing.detected_brand = result.brand
    listing.detected_model = result.model
    listing.variant = result.attributes
    listing.variant_key = result.variant_key
    listing.detected_size = result.attributes.get("size")
    listing.detected_material = result.attributes.get("material")
    listing.condition = result.condition
    listing.accessories = result.accessories
    listing.authenticity_info = result.authenticity_info
    listing.language = result.language
    listing.normalization_confidence = round(result.confidence, 3)
    listing.normalization_method = result.method
    listing.normalization_details = result.as_dict()


def normalize_listing(listing: Listing, normalizer: RuleNormalizer, ai: Any | None = None) -> NormalizationResult:
    result = normalizer.normalize(
        listing.title,
        listing.description or "",
        brand_hint=listing.brand_raw,
        model_hint=listing.model_raw,
        condition_hint=listing.condition_raw,
        category_hint=listing.category_raw,
    )
    if ai is not None:
        result = ai.maybe_improve(listing, result, normalizer)
    apply_normalization(listing, result)
    return result


def ingest_raw_listing(
    session: Session,
    raw: RawListing,
    *,
    source: str = ListingSource.CONNECTOR.value,
    is_demo: bool = False,
    now: datetime | None = None,
    fx: FxService | None = None,
    normalizer: RuleNormalizer | None = None,
    ai: Any | None = None,
    keep_raw_payload: bool = True,
) -> IngestResult:
    now = now or utcnow()
    fx = fx or FxService(session)
    normalizer = normalizer or normalizer_cache.get(session)
    marketplace_code = raw.marketplace if session.get(Marketplace, raw.marketplace) else "manual"

    listing = session.scalars(
        select(Listing).where(Listing.marketplace_code == marketplace_code, Listing.external_id == raw.external_id)
    ).first()
    price_eur, rate, rate_ts = fx.to_eur(raw.price, raw.currency)
    original_eur, _, _ = fx.to_eur(raw.original_price, raw.currency)
    content_hash = raw.content_hash()
    title = sanitize_text(raw.title, 500) or "(untitled)"
    description = sanitize_text(raw.description)

    if listing is None:
        listing = Listing(
            marketplace_code=marketplace_code,
            external_id=raw.external_id,
            first_seen_at=now,
            last_seen_at=now,
            source=source,
            is_demo=is_demo,
        )
        _copy_fields(listing, raw, title, description, price_eur, rate, rate_ts, original_eur, keep_raw_payload)
        listing.content_hash = content_hash
        if marketplace_code != raw.marketplace:
            listing.source_metadata = {**(listing.source_metadata or {}), "declared_marketplace": raw.marketplace}
        session.add(listing)
        session.flush()
        session.add(
            ListingPriceHistory(
                listing_id=listing.id,
                price_amount=raw.price,
                currency=raw.currency,
                price_eur=price_eur,
                fx_rate=rate,
                change_type="initial",
                observed_at=now,
            )
        )
        normalize_listing(listing, normalizer, ai)
        return IngestResult(listing, created=True, updated=False, price_changed=False)

    # ---- existing listing
    listing.last_seen_at = now
    updated = price_changed = False
    pct: float | None = None
    if raw.status in ("sold", "ended") and listing.status == "active":
        listing.status = raw.status
        listing.ended_at = now
        updated = True
    elif raw.status == "active" and listing.status in ("ended",):
        listing.status = "active"
        listing.ended_at = None
        updated = True

    if listing.content_hash != content_hash:
        old_price = listing.price_amount
        old_eur = listing.price_eur
        text_changed = (listing.title != title) or (listing.description != description)
        _copy_fields(listing, raw, title, description, price_eur, rate, rate_ts, original_eur, keep_raw_payload)
        listing.content_hash = content_hash
        updated = True
        if old_price is not None and abs(float(old_price) - float(raw.price)) >= 0.01:
            price_changed = True
            pct = (float(price_eur) - float(old_eur)) / float(old_eur) if old_eur else None
            change = "drop" if raw.price < old_price else "increase"
            session.add(
                ListingPriceHistory(
                    listing_id=listing.id,
                    price_amount=raw.price,
                    currency=raw.currency,
                    price_eur=price_eur,
                    fx_rate=rate,
                    change_type=change,
                    change_pct=round(pct, 4) if pct is not None else None,
                    observed_at=now,
                )
            )
            listing.last_price_change_at = now
            listing.last_price_change_pct = round(pct, 4) if pct is not None else None
            if change == "drop":
                listing.price_drop_count = (listing.price_drop_count or 0) + 1
        if text_changed:
            normalize_listing(listing, normalizer, ai)
    return IngestResult(listing, created=False, updated=updated, price_changed=price_changed, price_change_pct=pct)


def _copy_fields(listing: Listing, raw: RawListing, title: str, description: str, price_eur: float | None,
                 rate: float, rate_ts: datetime, original_eur: float | None, keep_raw: bool) -> None:
    listing.url = raw.url[:1024]
    listing.title = title
    listing.description = description
    listing.price_amount = raw.price
    listing.currency = raw.currency.upper()
    listing.price_eur = price_eur or 0.0
    listing.fx_rate = rate
    listing.fx_timestamp = rate_ts
    listing.original_price_amount = raw.original_price
    listing.original_price_eur = original_eur
    listing.price_kind = raw.price_kind
    if raw.sold_price is not None:
        listing.sold_price_eur = round(raw.sold_price * rate, 2)
        listing.sold_at = raw.sold_at
    listing.city = sanitize_text(raw.city, 120) or None
    listing.region = sanitize_text(raw.region, 120) or None
    listing.postal_code = raw.postal_code
    listing.country = (raw.country or "ES").upper()[:2]
    listing.seller_id = raw.seller_id
    listing.seller_name = sanitize_text(raw.seller_name, 200) or None
    listing.seller_rating = raw.seller_rating
    listing.seller_rating_count = raw.seller_rating_count
    listing.seller_account_created_at = raw.seller_account_created_at
    listing.seller_type = raw.seller_type
    listing.seller_listing_count = raw.seller_listing_count
    listing.condition_raw = raw.condition_raw
    listing.category_raw = sanitize_text(raw.category_raw, 200) or None
    listing.brand_raw = sanitize_text(raw.brand_raw, 120) or None
    listing.model_raw = sanitize_text(raw.model_raw, 200) or None
    listing.published_at = raw.published_at
    listing.shipping_available = raw.shipping_available
    listing.shipping_cost_eur = round(raw.shipping_cost * rate, 2) if raw.shipping_cost is not None else None
    listing.image_urls = [u for u in raw.image_urls if isinstance(u, str) and u.startswith(("http://", "https://"))][:12]
    if raw.status in ("sold", "ended", "reserved") and listing.status != raw.status:
        listing.status = raw.status
    listing.source_metadata = {**(listing.source_metadata or {}), **(raw.source_metadata or {})}
    if keep_raw and raw.raw is not None:
        listing.raw_payload = raw.raw


# ============================================================================ evaluation


def build_fee_engine(session: Session) -> FeeEngine:
    rules = [
        FeeRuleData(
            id=r.id, side=r.side, marketplace_code=r.marketplace_code, country=r.country, category_code=r.category_code,
            seller_type=r.seller_type, percent=r.percent or 0, fixed_eur=r.fixed_eur or 0,
            payment_percent=r.payment_percent or 0, payment_fixed_eur=r.payment_fixed_eur or 0,
            min_fee_eur=r.min_fee_eur, max_fee_eur=r.max_fee_eur,
        )
        for r in session.scalars(select(FeeRule).where(FeeRule.active.is_(True)))
    ]
    profiles = [
        CostProfileData(
            id=p.id, name=p.name, route=p.route, category_code=p.category_code, shipping_class=p.shipping_class,
            inbound_shipping_eur=p.inbound_shipping_eur or 0, outbound_shipping_eur=p.outbound_shipping_eur or 0,
            insurance_pct=p.insurance_pct or 0, import_duty_pct=p.import_duty_pct or 0,
            import_vat_pct=p.import_vat_pct or 0, misc_eur=p.misc_eur or 0, misc_pct=p.misc_pct or 0,
            travel_eur=p.travel_eur or 0,
        )
        for p in session.scalars(select(CostProfile).where(CostProfile.active.is_(True)))
    ]
    return FeeEngine(rules, profiles)


def category_costs(cat: Category) -> CategoryCosts:
    return CategoryCosts(
        code=cat.code,
        shipping_class=cat.shipping_class,
        refurbishment_eur=cat.refurbishment_eur or 0,
        authentication_eur=cat.authentication_eur or 0,
        authentication_required=cat.authentication_required,
    )


@dataclass
class CompRow:
    listing_id: int
    comparable: Comparable
    is_recent_exit: bool


class Evaluator:
    """Holds per-run caches; create one per batch."""

    def __init__(self, session: Session, now: datetime | None = None):
        self.session = session
        self.now = now or utcnow()
        self.business = get_setting(session, "business")
        self.scoring_cfg = scoring_config(session)
        self.valuation_engine = ValuationEngine(valuation_config(session))
        self.risk_engine = RiskEngine()
        self.fee_engine = build_fee_engine(session)
        self.categories = {c.code: c for c in session.scalars(select(Category))}
        self.products = {p.id: p for p in session.scalars(select(CanonicalProduct))}
        self.marketplaces = {m.code: m for m in session.scalars(select(Marketplace))}
        self._comps: dict[int, list[CompRow]] = {}
        self._dup: dict[str, Any] | None = None

    # ------------------------------------------------------------------ comparables
    def comparables(self, product_id: int) -> list[CompRow]:
        if product_id in self._comps:
            return self._comps[product_id]
        lookback = self.now - timedelta(days=int(self.business.get("comparable_lookback_days", 180)))
        rows = self.session.scalars(
            select(Listing).where(
                Listing.canonical_product_id == product_id,
                Listing.normalization_confidence >= MIN_COMPARABLE_CONFIDENCE,
                Listing.first_seen_at <= self.now,
                or_(Listing.status == "active", and_(Listing.status.in_(["sold", "ended"]), Listing.last_seen_at >= lookback)),
            )
        ).all()
        out = []
        for l in rows:
            if (l.normalization_details or {}).get("accessory_only"):
                continue
            start = aware(l.published_at) or aware(l.first_seen_at)
            ended_at = aware(l.ended_at)
            # evaluate "as of" self.now: a listing that ended later was still active then
            active_then = l.status == "active" or (ended_at is not None and ended_at > self.now)
            end = self.now if active_then else (ended_at or self.now)
            dom = max(0.0, (end - start).total_seconds() / 86400) if start else None
            sold = (l.price_kind == "sold" or l.status == "sold") and not active_then
            comp = Comparable(
                price_eur=float(l.sold_price_eur or l.price_eur) if sold else float(l.price_eur),
                kind="sold" if sold else ("asking" if active_then else "ended"),
                condition=l.condition,
                country=l.country,
                attributes=dict(l.variant or {}),
                observed_at=aware(l.sold_at) or start,
                days_on_market=dom,
                seller_type=l.seller_type,
                accessories=dict(l.accessories or {}),
                is_active=active_then,
                listing_id=l.id,
                marketplace=l.marketplace_code,
            )
            recent_exit = not active_then and ended_at is not None and ended_at >= self.now - timedelta(days=30)
            out.append(CompRow(l.id, comp, recent_exit))
        self._comps[product_id] = out
        return out

    def valuation_for(
        self,
        product: CanonicalProduct,
        market: str,
        *,
        attrs: dict[str, str],
        condition: str = "good",
        accessories: dict[str, bool] | None = None,
        exclude_listing_id: int | None = None,
    ) -> ValuationResult:
        cat = self.categories.get(product.category_code)
        comps = [c.comparable for c in self.comparables(product.id)]
        return self.valuation_engine.value(
            comps,
            target_attrs=attrs,
            variant_importance=dict(product.variant_attributes or {}),
            market=market,
            target_condition=condition,
            target_accessories=accessories,
            exclude_listing_id=exclude_listing_id,
            apply_accessory_premiums=bool(cat and cat.is_luxury),
            now=self.now,
        )

    # ------------------------------------------------------------------ duplicates (risk)
    def _dup_index(self) -> dict[str, Any]:
        if self._dup is None:
            images: dict[str, set[int]] = {}
            texts: dict[tuple[str, int], list[tuple[int, str | None]]] = {}
            sellers: dict[str, list[tuple[str | None, float]]] = {}
            rows = self.session.execute(
                select(Listing.id, Listing.image_urls, Listing.title, Listing.price_eur, Listing.city,
                       Listing.seller_id, Listing.canonical_product_id).where(Listing.status == "active")
            ).all()
            for lid, imgs, title, price, city, seller, pid in rows:
                for u in imgs or []:
                    images.setdefault(u, set()).add(lid)
                texts.setdefault((fold(title)[:80], int(round(float(price or 0) / 10))), []).append((lid, city))
                if seller:
                    cat = self.products[pid].category_code if pid in self.products else None
                    sellers.setdefault(seller, []).append((cat, float(price or 0)))
            self._dup = {"images": images, "texts": texts, "sellers": sellers}
        return self._dup

    def _dup_signals(self, listing: Listing) -> dict[str, int]:
        idx = self._dup_index()
        img_dups: set[int] = set()
        for u in listing.image_urls or []:
            img_dups |= idx["images"].get(u, set())
        img_dups.discard(listing.id)
        text_rows = [r for r in idx["texts"].get((fold(listing.title)[:80], int(round(float(listing.price_eur) / 10))), []) if r[0] != listing.id]
        cities = {c for _, c in text_rows if c and c != listing.city}
        seller_rows = idx["sellers"].get(listing.seller_id or "", [])
        high = [r for r in seller_rows if r[1] >= 500]
        return {
            "duplicate_image_listings": len(img_dups),
            "duplicate_text_listings": len(text_rows),
            "duplicate_text_cities": len(cities),
            "seller_high_value_listings": len(high),
            "seller_distinct_categories": len({c for c, _ in high if c}),
        }

    # ------------------------------------------------------------------ evaluate
    def resale_marketplace(self, category_code: str, resale_country: str) -> str:
        by_cat = self.business.get("category_resale_marketplace") or {}
        if category_code in by_cat:
            return by_cat[category_code]
        return (self.business.get("default_resale_marketplace") or {}).get(resale_country, "manual")

    def trade_context(self, listing: Listing, product: CanonicalProduct, resale_country: str) -> TradeContext:
        cat = self.categories[product.category_code]
        local_pickup = listing.country == resale_country and listing.shipping_available is False
        return TradeContext(
            source_marketplace=listing.marketplace_code,
            source_country=listing.country,
            resale_marketplace=self.resale_marketplace(cat.code, resale_country),
            resale_country=resale_country,
            category=category_costs(cat),
            listing_shipping_eur=listing.shipping_cost_eur,
            refurbishment_override_eur=product.refurbishment_eur,
            local_pickup=local_pickup,
        )

    def target_rois(self, product: CanonicalProduct) -> tuple[float, float]:
        cat = self.categories.get(product.category_code)
        target = product.target_roi or (cat.target_roi if cat else None) or float(self.business["target_roi"])
        min_roi = (cat.min_roi if cat else None) or float(self.business["min_roi"])
        return float(target), float(min(min_roi, target))

    def evaluate(self, listing: Listing, resale_country: str | None = None) -> list[Opportunity]:
        markets = [resale_country] if resale_country else list(self.business.get("resale_countries") or ["ES"])
        return [o for o in (self._evaluate_one(listing, m) for m in markets) if o is not None]

    def _existing(self, listing_id: int, market: str) -> Opportunity | None:
        return self.session.scalars(
            select(Opportunity).where(Opportunity.listing_id == listing_id, Opportunity.resale_country == market)
        ).first()

    def _evaluate_one(self, listing: Listing, market: str) -> Opportunity | None:
        opp = self._existing(listing.id, market)
        product = self.products.get(listing.canonical_product_id) if listing.canonical_product_id else None
        if listing.status != "active" or product is None or listing.normalization_confidence < MIN_MATCH_CONFIDENCE:
            if opp is not None:
                opp.is_active = False
                if listing.status != "active" and opp.status in ("DISCOVERED", "WATCHING"):
                    opp.status = "EXPIRED"
            return opp
        cat = self.categories[product.category_code]
        price = float(listing.price_eur)
        val = self.valuation_for(
            product, market, attrs=dict(listing.variant or {}), condition=listing.condition,
            accessories=dict(listing.accessories or {}), exclude_listing_id=listing.id,
        )
        ctx = self.trade_context(listing, product, market)
        target_roi, min_roi = self.target_rois(product)
        quick = val.quick_sale_eur
        market_value = val.market_value_eur

        econ_quick = self.fee_engine.economics(price, quick, ctx) if quick else None
        econ_market = self.fee_engine.economics(price, market_value, ctx) if market_value else None
        max_buy = (
            self.fee_engine.max_buy_price(quick, ctx, target_roi=target_roi, min_profit_eur=float(self.business.get("min_profit_eur", 0)))
            if quick else None
        )
        discount = (1 - price / market_value) if market_value else None

        comps = self.comparables(product.id)
        liq = estimate_liquidity(
            LiquidityInput(
                n_active_comparables=sum(1 for c in comps if c.comparable.is_active),
                n_sold_recent=sum(1 for c in comps if c.is_recent_exit),
                median_days_on_market=val.median_days_on_market,
                popularity=float(product.popularity or 0.5),
                base_holding_days=float(product.typical_holding_days or cat.base_holding_days or 21),
            ),
            self.scoring_cfg,
        )
        route = self.fee_engine.route(listing.country, market)
        holding = liq.expected_holding_days_quick + self.scoring_cfg.transit_days.get(route, 5)
        if cat.authentication_required:
            holding += self.scoring_cfg.authentication_days

        started = aware(listing.published_at) or aware(listing.first_seen_at) or self.now
        age_days = max(0.0, (self.now - started).total_seconds() / 86400)
        fresh_from = max(started, aware(listing.last_price_change_at) or started) if (listing.last_price_change_pct or 0) < 0 else started
        fresh_age_hours = max(0.0, (self.now - fresh_from).total_seconds() / 3600)

        mp = self.marketplaces.get(listing.marketplace_code)
        risk = self.risk_engine.evaluate(
            RiskInput(
                title=listing.title,
                description=listing.description or "",
                price_eur=price,
                market_value_eur=market_value if val.is_usable else None,
                quick_sale_eur=quick,
                valuation_confidence=val.confidence_level,
                country=listing.country,
                city=listing.city,
                marketplace_country=mp.country if mp and mp.code != "manual" else None,
                seller_rating=listing.seller_rating,
                seller_rating_count=listing.seller_rating_count,
                seller_account_created_at=aware(listing.seller_account_created_at),
                seller_type=listing.seller_type,
                image_urls=list(listing.image_urls or []),
                is_luxury=cat.is_luxury,
                accessories=dict(listing.accessories or {}),
                authenticity_info=listing.authenticity_info,
                attributes=dict(listing.variant or {}),
                known_references=list(product.reference_numbers or []),
                normalization_confidence=listing.normalization_confidence,
                normalization_reasons=list((listing.normalization_details or {}).get("reasons") or []),
                accessory_only=bool((listing.normalization_details or {}).get("accessory_only")),
                shipping_available=listing.shipping_available,
                now=self.now,
                **self._dup_signals(listing),
            )
        )

        opp_type, target_offer, reason = classify_opportunity(
            asking=price,
            max_buy_price=max_buy or 0.0,
            market_value=market_value if val.is_usable else None,
            net_profit_at_ask=econ_quick.net_profit if econ_quick else None,
            roi_at_ask=econ_quick.roi if econ_quick else None,
            min_roi=min_roi,
            source_country=listing.country,
            resale_country=market,
            listing_age_days=age_days,
            price_drops=listing.price_drop_count or 0,
            cfg=self.scoring_cfg,
        )
        profit_at_target = None
        score_econ = econ_quick
        if opp_type == OpportunityType.NEGOTIATION.value and target_offer and quick:
            score_econ = self.fee_engine.economics(target_offer, quick, ctx)
            profit_at_target = score_econ.net_profit
        vel = velocity_metrics(score_econ.net_profit, score_econ.capital, holding) if score_econ else None
        score = compute_score(
            ScoreInput(
                purchase_price=score_econ.purchase_price if score_econ else price,
                market_value=market_value,
                quick_sale=quick,
                net_profit=score_econ.net_profit if score_econ else None,
                roi=score_econ.roi if score_econ else None,
                liquidity_score=liq.score,
                listing_age_hours=fresh_age_hours,
                valuation_confidence_score=val.confidence_score,
                valuation_confidence_level=val.confidence_level,
                normalization_confidence=listing.normalization_confidence,
                risk_score=risk.score,
                risk_level=risk.level,
                annualized_roi=vel.annualized_roi if vel else None,
                opportunity_type=opp_type,
            ),
            self.scoring_cfg,
        )

        valuation_id = self._latest_valuation_id(product.id, listing.variant_key or "", market)
        is_new = opp is None
        if opp is None:
            opp = Opportunity(listing_id=listing.id, resale_country=market, status="DISCOVERED")
        opp.canonical_product_id = product.id
        opp.valuation_id = valuation_id
        opp.opportunity_type = opp_type
        opp.source_country = listing.country
        opp.is_active = opp_type != OpportunityType.NONE.value and opp.status not in ("REJECTED", "EXPIRED", "SOLD")
        opp.purchase_price_eur = price
        opp.quick_sale_eur = quick
        opp.market_value_eur = market_value
        costs = econ_quick.costs if econ_quick else None
        opp.buy_costs_eur = costs.total("buy") + costs.total("prep") if costs else 0
        opp.sell_costs_eur = costs.total("sell") if costs else 0
        opp.total_costs_eur = costs.total() if costs else 0
        opp.cost_breakdown = {**(costs.as_dict() if costs else {}), "route": route, "resale_marketplace": ctx.resale_marketplace, "capital": econ_quick.capital if econ_quick else None}
        opp.net_profit_quick_eur = econ_quick.net_profit if econ_quick else None
        opp.net_profit_market_eur = econ_market.net_profit if econ_market else None
        opp.roi = econ_quick.roi if econ_quick else None
        opp.discount_pct = round(discount, 4) if discount is not None else None
        opp.max_buy_price_eur = max_buy
        opp.target_offer_eur = target_offer
        opp.profit_at_target_offer_eur = profit_at_target
        opp.expected_holding_days = vel.holding_days if vel else round(holding, 1)
        opp.annualized_roi = vel.annualized_roi if vel else None
        opp.profit_velocity = vel.profit_velocity if vel else None
        opp.capital_efficiency = vel.capital_efficiency if vel else None
        opp.profit_per_1000 = vel.profit_per_1000 if vel else None
        opp.liquidity_score = liq.score
        opp.liquidity_label = liq.label
        opp.confidence_score = val.confidence_score
        opp.confidence_level = val.confidence_level
        opp.normalization_confidence = listing.normalization_confidence
        opp.risk_level = risk.level
        opp.risk_score = risk.score
        opp.risk_flags = [f.as_dict() for f in risk.flags]
        opp.requires_authentication = risk.requires_authentication
        opp.score = score.score
        opp.score_components = {
            **score.components,
            "caps": score.caps_applied,
            "liquidity_signals": liq.signals,
            "valuation": {
                "n": val.n_comparables, "n_sold": val.n_sold, "dispersion": val.dispersion,
                "p25": val.p25_eur, "p75": val.p75_eur, "median": val.median_eur, "notes": val.notes,
            },
            "listing_age_days": round(age_days, 2),
            "target_roi": target_roi,
            "min_roi": min_roi,
        }
        opp.explanation = [reason, *score.explanation, *val.notes]
        opp.computed_at = self.now
        opp.fingerprint = hashlib.sha1(f"{round(price, 2)}|{opp_type}".encode()).hexdigest()
        if is_new:
            self.session.add(opp)
        return opp

    def _latest_valuation_id(self, product_id: int, variant_key: str, market: str) -> int | None:
        return self.session.scalar(
            select(Valuation.id)
            .where(Valuation.canonical_product_id == product_id, Valuation.variant_key == variant_key, Valuation.market == market)
            .order_by(Valuation.computed_at.desc())
            .limit(1)
        )

    # ------------------------------------------------------------------ valuation snapshots
    def snapshot_valuations(self, product: CanonicalProduct) -> list[Valuation]:
        """Append a market snapshot per (variant, market) - feeds the product page & history."""
        keys = {
            vk or ""
            for (vk,) in self.session.execute(
                select(Listing.variant_key).where(Listing.canonical_product_id == product.id).distinct()
            )
        }
        keys.add("")
        out = []
        for market in self.business.get("resale_countries") or ["ES"]:
            for key in sorted(keys):
                attrs = parse_variant_key(key)
                res = self.valuation_for(product, market, attrs=attrs)
                if res.n_comparables == 0:
                    continue
                v = Valuation(
                    canonical_product_id=product.id,
                    variant_key=key,
                    market=market,
                    computed_at=self.now,
                    n_comparables=res.n_comparables,
                    n_sold=res.n_sold,
                    n_outliers=res.n_outliers,
                    median_eur=res.median_eur,
                    trimmed_mean_eur=res.trimmed_mean_eur,
                    p25_eur=res.p25_eur,
                    p75_eur=res.p75_eur,
                    lowest_reasonable_eur=res.lowest_reasonable_eur,
                    quick_sale_eur=res.quick_sale_eur,
                    market_value_eur=res.market_value_eur,
                    opportunistic_buy_eur=res.opportunistic_buy_eur,
                    dispersion=res.dispersion,
                    confidence_score=res.confidence_score,
                    confidence_level=res.confidence_level,
                    median_days_on_market=res.median_days_on_market,
                    details={"by_country": res.by_country, "by_marketplace": res.by_marketplace, "notes": res.notes, "effective_n": res.effective_n},
                )
                self.session.add(v)
                out.append(v)
        self.session.flush()
        return out


def evaluate_all(session: Session, *, only_ids: list[int] | None = None, now: datetime | None = None) -> int:
    ev = Evaluator(session, now=now)
    q = select(Listing).where(Listing.canonical_product_id.is_not(None))
    if only_ids is not None:
        q = q.where(Listing.id.in_(only_ids))
    n = 0
    for listing in session.scalars(q).all():
        ev.evaluate(listing)
        n += 1
    session.flush()
    return n


def snapshot_all_valuations(session: Session, now: datetime | None = None) -> int:
    ev = Evaluator(session, now=now)
    n = 0
    for product in ev.products.values():
        if product.is_active:
            n += len(ev.snapshot_valuations(product))
    return n
