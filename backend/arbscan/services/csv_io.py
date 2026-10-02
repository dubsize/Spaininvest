"""Human-readable CSV import / export.

* Exports use clear column names, EUR amounts with 2 decimals, ISO dates, ``;``-free
  values (standard comma CSV, UTF-8 with BOM so Excel opens accents correctly).
* Imports are tolerant: unknown columns are ignored, errors are reported per row.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from arbscan.connectors.base import RawListing
from arbscan.connectors.page_metadata import detect_marketplace, external_id_from_url
from arbscan.db.models import CanonicalProduct, Listing, ListingPriceHistory, Opportunity, Watchlist
from arbscan.normalization.text import sanitize_text
from arbscan.services.pipeline import Evaluator, ingest_raw_listing

BOM = "﻿"


def _fmt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.2f}"
    if isinstance(v, datetime):
        return v.astimezone(UTC).strftime("%Y-%m-%d %H:%M")
    if isinstance(v, list):
        return " | ".join(str(x) for x in v)
    return str(v)


def _write(rows: list[dict[str, Any]], columns: list[str]) -> str:
    buf = io.StringIO()
    buf.write(BOM)
    w = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: _fmt(r.get(k)) for k in columns})
    return buf.getvalue()


DEAL_COLUMNS = [
    "opportunity_id", "type", "status", "score", "product", "listing_title", "marketplace", "country", "city",
    "price_eur", "market_value_eur", "quick_sale_eur", "net_profit_eur", "roi_pct", "discount_pct",
    "max_buy_price_eur", "target_offer_eur", "liquidity", "risk", "risk_reasons", "confidence",
    "listing_age_days", "url", "first_seen", "published",
]


def export_opportunities(session: Session, include_inactive: bool = False) -> str:
    q = select(Opportunity).order_by(Opportunity.score.desc())
    if not include_inactive:
        q = q.where(Opportunity.is_active.is_(True))
    rows = []
    for o in session.scalars(q):
        l = o.listing
        rows.append({
            "opportunity_id": o.id, "type": o.opportunity_type, "status": o.status, "score": o.score,
            "product": o.canonical_product.name if o.canonical_product else "", "listing_title": l.title,
            "marketplace": l.marketplace_code, "country": l.country, "city": l.city, "price_eur": o.purchase_price_eur,
            "market_value_eur": o.market_value_eur, "quick_sale_eur": o.quick_sale_eur,
            "net_profit_eur": o.net_profit_quick_eur, "roi_pct": (o.roi or 0) * 100 if o.roi is not None else None,
            "discount_pct": (o.discount_pct or 0) * 100 if o.discount_pct is not None else None,
            "max_buy_price_eur": o.max_buy_price_eur, "target_offer_eur": o.target_offer_eur,
            "liquidity": o.liquidity_label, "risk": o.risk_level,
            "risk_reasons": [f["message"] for f in o.risk_flags or [] if f.get("points", 0) > 0],
            "confidence": o.confidence_level, "listing_age_days": (o.score_components or {}).get("listing_age_days"),
            "url": l.url, "first_seen": l.first_seen_at, "published": l.published_at,
        })
    return _write(rows, DEAL_COLUMNS)


HISTORY_COLUMNS = ["product", "listing_id", "marketplace", "country", "listing_title", "observed_at", "price", "currency", "price_eur", "change", "change_pct", "url"]


def export_price_history(session: Session, product_id: int | None = None) -> str:
    q = select(ListingPriceHistory, Listing).join(Listing, Listing.id == ListingPriceHistory.listing_id)
    if product_id:
        q = q.where(Listing.canonical_product_id == product_id)
    q = q.order_by(Listing.id, ListingPriceHistory.observed_at)
    rows = []
    for h, l in session.execute(q):
        rows.append({
            "product": l.canonical_product.name if l.canonical_product else "", "listing_id": l.id,
            "marketplace": l.marketplace_code, "country": l.country, "listing_title": l.title, "observed_at": h.observed_at,
            "price": h.price_amount, "currency": h.currency, "price_eur": h.price_eur, "change": h.change_type,
            "change_pct": (h.change_pct * 100) if h.change_pct is not None else None, "url": l.url,
        })
    return _write(rows, HISTORY_COLUMNS)


WATCHLIST_COLUMNS = ["name", "keyword", "product_slug", "category", "brands", "countries", "marketplaces", "max_price_eur", "min_discount_pct", "min_profit_eur", "min_roi_pct", "min_score", "priority", "scan_interval_minutes", "enabled"]


def export_watchlists(session: Session) -> str:
    rows = []
    for w in session.scalars(select(Watchlist)):
        rows.append({
            "name": w.name, "keyword": w.keyword, "product_slug": w.canonical_product.slug if w.canonical_product else "",
            "category": w.category_code, "brands": w.brands, "countries": w.countries, "marketplaces": w.marketplaces,
            "max_price_eur": w.max_price_eur, "min_discount_pct": (w.min_discount or 0) * 100 if w.min_discount is not None else None,
            "min_profit_eur": w.min_profit_eur, "min_roi_pct": (w.min_roi or 0) * 100 if w.min_roi is not None else None,
            "min_score": w.min_score, "priority": w.priority, "scan_interval_minutes": w.scan_interval_minutes, "enabled": "yes" if w.enabled else "no",
        })
    return _write(rows, WATCHLIST_COLUMNS)


# ---------------------------------------------------------------------------- import


def _read(text: str) -> list[dict[str, str]]:
    text = text.lstrip(BOM)
    sample = text[:2000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(io.StringIO(text), dialect=dialect)]


def _num(v: str | None) -> float | None:
    if v is None or v == "":
        return None
    v = v.replace("€", "").replace(" ", "").replace("\xa0", "")
    if "," in v and "." in v:
        v = v.replace(".", "").replace(",", ".") if v.rfind(",") > v.rfind(".") else v.replace(",", "")
    elif "," in v:
        v = v.replace(",", ".")
    return float(v)


def _list(v: str | None) -> list[str]:
    if not v:
        return []
    for sep in ("|", ";", ","):
        if sep in v:
            return [x.strip() for x in v.split(sep) if x.strip()]
    return [v.strip()]


def _date(v: str | None) -> datetime | None:
    if not v:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(v, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None


def import_watchlists(session: Session, text: str) -> dict[str, Any]:
    created, errors = 0, []
    sp = None
    products = {p.slug: p.id for p in session.scalars(select(CanonicalProduct))}
    for i, r in enumerate(_read(text), start=2):
        try:
            name = r.get("name") or r.get("keyword")
            if not name:
                raise ValueError("name or keyword required")
            def pct(k: str, row: dict[str, str] = r) -> float | None:
                v = _num(row.get(k))
                return v / 100 if v is not None else None

            sp = session.begin_nested()
            session.add(Watchlist(
                name=sanitize_text(name, 160), keyword=sanitize_text(r.get("keyword"), 200),
                canonical_product_id=products.get(r.get("product_slug", "")), category_code=r.get("category") or None,
                brands=_list(r.get("brands")), countries=[c.upper() for c in _list(r.get("countries"))],
                marketplaces=_list(r.get("marketplaces")), max_price_eur=_num(r.get("max_price_eur")),
                min_discount=pct("min_discount_pct"), min_profit_eur=_num(r.get("min_profit_eur")), min_roi=pct("min_roi_pct"),
                min_score=_num(r.get("min_score")), priority=(r.get("priority") or "standard").lower(),
                scan_interval_minutes=int(_num(r.get("scan_interval_minutes")) or 0) or None,
                enabled=(r.get("enabled", "yes").lower() not in ("no", "false", "0")),
            ))
            sp.commit()
            created += 1
        except Exception as exc:  # noqa: BLE001
            if sp is not None and sp.is_active:
                sp.rollback()
            errors.append({"row": i, "error": str(exc)})
    return {"created": created, "errors": errors}


LISTING_IMPORT_COLUMNS = ["url", "title", "price", "currency", "marketplace", "country", "city", "description", "condition", "seller_name", "seller_rating", "seller_rating_count", "published_at", "shipping_cost", "image_url", "price_kind", "sold_price", "sold_at", "status"]


def import_listings(session: Session, text: str) -> dict[str, Any]:
    created, updated, errors, ids = 0, 0, [], []
    for i, r in enumerate(_read(text), start=2):
        try:
            url = r.get("url", "")
            title = r.get("title")
            price = _num(r.get("price"))
            if not title or price is None:
                raise ValueError("title and price are required")
            mp_detected, country_detected = detect_marketplace(url) if url else ("manual", None)
            kind = (r.get("price_kind") or "asking").lower()
            raw = RawListing(
                marketplace=r.get("marketplace") or mp_detected,
                external_id=r.get("external_id") or (external_id_from_url(url) if url else f"csv-{abs(hash((title, price)))}"),
                url=url, title=title, price=price, currency=(r.get("currency") or "EUR").upper(),
                country=(r.get("country") or country_detected or "ES").upper(), city=r.get("city") or None,
                description=r.get("description", ""), condition_raw=r.get("condition") or None,
                seller_name=r.get("seller_name") or None, seller_rating=_num(r.get("seller_rating")),
                seller_rating_count=int(_num(r.get("seller_rating_count")) or 0) if r.get("seller_rating_count") else None,
                published_at=_date(r.get("published_at")), shipping_cost=_num(r.get("shipping_cost")),
                image_urls=_list(r.get("image_url")), price_kind="sold" if kind == "sold" else "asking",
                sold_price=_num(r.get("sold_price")) or (price if kind == "sold" else None),
                sold_at=_date(r.get("sold_at")), status=(r.get("status") or ("sold" if kind == "sold" else "active")).lower(),
                source_metadata={"imported": "csv"},
            )
            with session.begin_nested():
                res = ingest_raw_listing(session, raw, source="csv")
            created += res.created
            updated += (not res.created)
            ids.append(res.listing.id)
        except Exception as exc:  # noqa: BLE001
            errors.append({"row": i, "error": str(exc)})
    session.flush()
    ev = Evaluator(session)
    for l in session.scalars(select(Listing).where(Listing.id.in_(ids))):
        ev.evaluate(l)
    return {"created": created, "updated": updated, "errors": errors, "listing_ids": ids}
