"""Idempotent seeding of reference data and (optionally) demo data."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from arbscan.alerts.service import ensure_default_rules
from arbscan.connectors.base import StubConnector
from arbscan.connectors.registry import CONNECTORS, MARKETPLACE_SEED
from arbscan.core.logging import get_logger
from arbscan.db.models import (
    AlertEvent,
    CanonicalProduct,
    Category,
    CostProfile,
    Deal,
    FeeRule,
    Listing,
    ListingPriceHistory,
    Marketplace,
    Opportunity,
    ScanRun,
    StatusEvent,
    Valuation,
    Watchlist,
)
from arbscan.normalization.catalog import load_seed_yaml, normalizer_cache
from arbscan.services.fx import FxService, seed_static_rates
from arbscan.services.pipeline import Evaluator, ingest_raw_listing, snapshot_all_valuations

log = get_logger(__name__)
DATA = Path(__file__).resolve().parent / "data"

PRODUCT_FIELDS = (
    "name", "brand", "model", "collection", "product_type", "brand_aliases", "aliases", "patterns",
    "attribute_rules", "reference_numbers", "required_keywords", "excluded_keywords", "variant_attributes",
    "retail_price_eur", "popularity", "typical_holding_days", "refurbishment_eur", "target_roi",
)

DEFAULT_WATCHLISTS: list[dict[str, Any]] = [
    {"name": "Thermomix TM6 - Spain & Germany", "keyword": "Thermomix TM6", "product": "thermomix-tm6", "countries": ["ES", "DE"], "max_price_eur": 700, "min_profit_eur": 80, "priority": "high"},
    {"name": "Cartier Love - EU", "keyword": "Cartier Love", "product": "cartier-love-bracelet", "countries": ["ES", "FR", "DE"], "min_profit_eur": 300, "priority": "high"},
    {"name": "Rolex Datejust", "keyword": "Rolex Datejust", "product": "rolex-datejust", "min_profit_eur": 400, "priority": "standard"},
    {"name": "Omega Speedmaster", "keyword": "Omega Speedmaster", "product": "omega-speedmaster-moonwatch", "priority": "standard"},
    {"name": "LV Neverfull / Speedy", "keyword": "Louis Vuitton Neverfull", "product": "lv-neverfull", "countries": ["ES", "FR"], "priority": "standard"},
    {"name": "Chanel Classic Flap", "keyword": "Chanel Classic Flap", "product": "chanel-classic-flap-medium", "priority": "standard"},
    {"name": "Fujifilm X100V / VI", "keyword": "Fujifilm X100V", "product": "fujifilm-x100v", "priority": "high", "min_roi": 0.15},
    {"name": "PS5 deals", "keyword": "PS5", "product": "ps5", "countries": ["ES"], "max_price_eur": 400, "priority": "standard"},
    {"name": "Sonos Arc", "keyword": "Sonos Arc", "product": "sonos-arc", "priority": "standard"},
    {"name": "MacBook Pro Apple Silicon", "keyword": "MacBook Pro M1 Pro", "product": "apple-macbook-pro", "priority": "standard"},
    {"name": "Retired LEGO Star Wars", "keyword": "LEGO 10221", "product": "lego-10221-super-star-destroyer", "category": "lego", "priority": "background"},
    {"name": "Bugaboo Fox (local)", "keyword": "Bugaboo Fox", "product": "bugaboo-fox", "countries": ["ES"], "priority": "standard"},
    {"name": "Brompton", "keyword": "Brompton", "product": "brompton-c-line", "priority": "background"},
]


def seed_reference_data(session: Session) -> dict[str, int]:
    counts: dict[str, int] = {}
    catalog = load_seed_yaml()

    for c in catalog["categories"]:
        row = session.get(Category, c["code"])
        if row is None:
            session.add(Category(**c))
            counts["categories"] = counts.get("categories", 0) + 1
    session.flush()

    for p in catalog["products"]:
        if session.scalars(select(CanonicalProduct).where(CanonicalProduct.slug == p["slug"])).first():
            continue
        data = {k: p[k] for k in PRODUCT_FIELDS if k in p}
        data["reference_numbers"] = [str(r) for r in data.get("reference_numbers", [])]
        if not data.get("retail_price_eur"):
            data["retail_price_eur"] = None
        session.add(CanonicalProduct(slug=p["slug"], category_code=p["category"], **data))
        counts["products"] = counts.get("products", 0) + 1
    session.flush()
    normalizer_cache.invalidate()

    for m in MARKETPLACE_SEED:
        if session.get(Marketplace, m["code"]):
            continue
        cls = CONNECTORS[m["connector_key"]]
        is_stub = issubclass(cls, StubConnector)
        session.add(Marketplace(
            code=m["code"], name=m["name"], country=m["country"], connector_key=m["connector_key"],
            base_url=m.get("base_url", ""), config=m.get("config", {}), enabled=m.get("enabled", False),
            status="STUB" if is_stub else "NOT_CONFIGURED",
            poll_interval_seconds=m.get("poll_interval_seconds", cls.default_poll_seconds),
            max_requests_per_minute=m.get("max_requests_per_minute", cls.default_requests_per_minute),
            supports_sold_data=cls.supports_sold_data,
            compliance_notes=f"[{cls.compliance.method}] {cls.compliance.summary}"
            + (f"\nAlternative: {cls.compliance.alternative}" if cls.compliance.alternative else ""),
        ))
        counts["marketplaces"] = counts.get("marketplaces", 0) + 1
    session.flush()

    if session.scalars(select(FeeRule).limit(1)).first() is None:
        fees = yaml.safe_load((DATA / "fees.yaml").read_text(encoding="utf-8"))
        for r in fees["fee_rules"]:
            session.add(FeeRule(source="seed (approximate)", verified=False, **r))
        for p in fees["cost_profiles"]:
            session.add(CostProfile(**p))
        counts["fee_rules"] = len(fees["fee_rules"])
        counts["cost_profiles"] = len(fees["cost_profiles"])

    seed_static_rates(session)
    ensure_default_rules(session)

    if session.scalars(select(Watchlist).limit(1)).first() is None:
        slugs = {p.slug: p.id for p in session.scalars(select(CanonicalProduct))}
        for w in DEFAULT_WATCHLISTS:
            w = dict(w)
            pid = slugs.get(w.pop("product", ""))
            cat = w.pop("category", None)
            session.add(Watchlist(canonical_product_id=pid, category_code=cat, **w))
        counts["watchlists"] = len(DEFAULT_WATCHLISTS)
    session.flush()
    return counts


def seed_demo_data(session: Session, seed: int = 42, now: datetime | None = None) -> dict[str, int]:
    """Create demo listings (with price histories), valuations, opportunities and deals."""
    from arbscan.seed.demo import generate_demo_listings

    if session.scalars(select(Listing.id).where(Listing.is_demo.is_(True)).limit(1)).first():
        return {"skipped": 1}
    now = now or datetime.now(UTC)
    fx = FxService(session)
    normalizer = normalizer_cache.get(session)
    demos = generate_demo_listings(seed=seed, now=now)
    for d in demos:
        timeline = d.price_timeline or [(d.first_seen_at, d.raw.price)]
        final_price = d.raw.price
        for i, (ts, price) in enumerate(timeline):
            d.raw.price = float(price)
            res = ingest_raw_listing(session, d.raw, source="demo", is_demo=True, now=max(ts, d.first_seen_at) if i == 0 else ts, fx=fx, normalizer=normalizer)
        d.raw.price = final_price
        l = res.listing
        l.first_seen_at = d.first_seen_at
        l.last_seen_at = d.ended_at or now
        if d.ended_at:
            l.status = "ended"
            l.ended_at = d.ended_at
    session.flush()

    # historical snapshots (as-of each date, using listings known at that time) feed price trends
    n_val = 0
    for days_ago in (90, 60, 45, 30, 14, 7, 0):
        n_val += snapshot_all_valuations(session, now=now - timedelta(days=days_ago))
    ev = Evaluator(session, now=now)
    n_opp = 0
    for l in session.scalars(select(Listing).where(Listing.status == "active", Listing.canonical_product_id.is_not(None))):
        n_opp += len(ev.evaluate(l))
    session.flush()
    n_deals = _seed_demo_deals(session, now)
    log.info("demo data seeded", extra={"listings": len(demos), "valuations": n_val, "opportunities": n_opp, "deals": n_deals})
    return {"listings": len(demos), "valuations": n_val, "opportunities": n_opp, "deals": n_deals}


def _seed_demo_deals(session: Session, now: datetime) -> int:
    rows = [
        # title, category, marketplace, country, buy, days_ago_bought, costs(ship, repair, auth, other), sold?(price, days_after, fees, ship)
        ("Vorwerk Thermomix TM6", "kitchen_appliances", "wallapop", "ES", 560, 74, (0, 15, 0, 0), (790, 6, 0, 0)),
        ("Vorwerk Thermomix TM6", "kitchen_appliances", "ebay_de", "DE", 610, 45, (28, 10, 0, 0), (820, 9, 0, 0)),
        ("Fujifilm X100V", "cameras", "wallapop", "ES", 1080, 60, (6, 0, 0, 0), (1390, 4, 0, 0)),
        ("Louis Vuitton Neverfull", "luxury_bags", "leboncoin", "FR", 820, 95, (40, 30, 45, 0), (1190, 21, 0, 15)),
        ("Sony PlayStation 5", "gaming", "wallapop", "ES", 290, 30, (0, 0, 0, 0), (375, 3, 0, 0)),
        ("Omega Speedmaster Moonwatch Professional", "luxury_watches", "ebay_fr", "FR", 4300, 120, (35, 0, 120, 0), (5150, 33, 0, 15)),
        ("Bugaboo Fox", "strollers", "wallapop", "ES", 380, 12, (0, 25, 0, 10), None),
        ("Cartier Love Bracelet", "luxury_jewelry", "leboncoin", "FR", 4100, 40, (35, 60, 80, 0), None),
        ("Apple MacBook Pro (Apple Silicon)", "computers", "ebay_es", "ES", 1190, 75, (8, 0, 0, 0), None),
    ]
    slugs = {p.name: p for p in session.scalars(select(CanonicalProduct))}
    for title, cat, mp, country, buy, ago, (ship, repair, auth, other), sold in rows:
        prod = slugs.get(title)
        bought = now - timedelta(days=ago)
        d = Deal(
            title=title, category_code=cat, source_marketplace=mp, source_country=country,
            canonical_product_id=prod.id if prod else None, status="PURCHASED", purchase_price_eur=buy,
            purchase_date=bought, purchase_shipping_eur=ship, repair_cost_eur=repair,
            authentication_cost_eur=auth, other_purchase_cost_eur=other,
            expected_sale_price_eur=round(buy * 1.3, -1), notes="demo deal",
        )
        d.expected_profit_eur = round(d.expected_sale_price_eur - buy - ship - repair - auth - other, 2)
        if sold:
            price, after, fees, sship = sold
            d.status = "SOLD"
            d.sale_price_eur = price
            d.sale_date = bought + timedelta(days=after)
            d.sale_marketplace = "wallapop"
            d.sale_fees_eur = fees
            d.sale_shipping_eur = sship
        else:
            d.status = "LISTED_FOR_RESALE" if ago > 30 else "RECEIVED"
        session.add(d)
    session.flush()
    return len(rows)


def purge_demo_data(session: Session) -> int:
    ids = [i for (i,) in session.execute(select(Listing.id).where(Listing.is_demo.is_(True)))]
    if not ids:
        return 0
    session.execute(delete(AlertEvent).where(AlertEvent.listing_id.in_(ids)))
    session.execute(delete(Opportunity).where(Opportunity.listing_id.in_(ids)))
    session.execute(delete(ListingPriceHistory).where(ListingPriceHistory.listing_id.in_(ids)))
    session.execute(delete(Listing).where(Listing.id.in_(ids)))
    session.execute(delete(Deal).where(Deal.notes == "demo deal"))
    session.execute(delete(Valuation))
    session.execute(delete(ScanRun).where(ScanRun.marketplace_code == "demo_feed"))
    session.execute(delete(StatusEvent).where(StatusEvent.entity == "opportunity"))
    demo_mp = session.get(Marketplace, "demo_feed")
    if demo_mp:
        demo_mp.enabled = False
    snapshot_all_valuations(session)
    return len(ids)
