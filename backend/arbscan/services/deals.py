"""Deal tracker (PURCHASED -> SOLD) and portfolio analytics."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from arbscan.db.enums import INVENTORY_STATUSES, DealStatus
from arbscan.db.models import Deal, Opportunity, StatusEvent

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DISCOVERED": {"WATCHING", "CONTACTED", "NEGOTIATING", "PURCHASED", "REJECTED", "SCAM_RISK", "EXPIRED"},
    "WATCHING": {"CONTACTED", "NEGOTIATING", "PURCHASED", "REJECTED", "SCAM_RISK", "EXPIRED", "DISCOVERED"},
    "CONTACTED": {"NEGOTIATING", "PURCHASED", "REJECTED", "SCAM_RISK", "EXPIRED", "WATCHING"},
    "NEGOTIATING": {"PURCHASED", "REJECTED", "SCAM_RISK", "EXPIRED", "CONTACTED", "WATCHING"},
    "PURCHASED": {"RECEIVED", "LISTED_FOR_RESALE", "SOLD"},
    "RECEIVED": {"LISTED_FOR_RESALE", "SOLD"},
    "LISTED_FOR_RESALE": {"SOLD", "RECEIVED"},
    "SOLD": set(),
    "REJECTED": {"DISCOVERED", "WATCHING"},
    "SCAM_RISK": {"DISCOVERED", "WATCHING", "REJECTED"},
    "EXPIRED": {"DISCOVERED", "WATCHING"},
}


class TransitionError(ValueError):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


def _aware(dt: datetime | None) -> datetime | None:
    return None if dt is None else (dt if dt.tzinfo else dt.replace(tzinfo=UTC))


def log_status(session: Session, entity: str, entity_id: int, old: str | None, new: str, note: str = "") -> None:
    session.add(StatusEvent(entity=entity, entity_id=entity_id, from_status=old, to_status=new, note=note))


def set_opportunity_status(session: Session, opp: Opportunity, new: str, note: str = "") -> Opportunity:
    new = DealStatus(new).value
    old = opp.status
    if new == old:
        return opp
    if new not in ALLOWED_TRANSITIONS.get(old, set()):
        raise TransitionError(f"cannot move opportunity from {old} to {new}")
    opp.status = new
    if new in ("REJECTED", "SCAM_RISK", "EXPIRED"):
        opp.is_active = False
    elif new in ("DISCOVERED", "WATCHING") and opp.opportunity_type != "NONE":
        opp.is_active = True
    log_status(session, "opportunity", opp.id, old, new, note)
    return opp


def purchase_opportunity(session: Session, opp: Opportunity, data: dict[str, Any]) -> Deal:
    if opp.status not in ("PURCHASED",):
        set_opportunity_status(session, opp, "PURCHASED", "purchased")
    listing = opp.listing
    product = opp.canonical_product
    deal = Deal(
        opportunity_id=opp.id,
        listing_id=listing.id,
        canonical_product_id=opp.canonical_product_id,
        title=product.name if product else listing.title,
        category_code=product.category_code if product else None,
        source_marketplace=listing.marketplace_code,
        source_country=listing.country,
        status="PURCHASED",
        purchase_price_eur=data.get("purchase_price_eur", opp.purchase_price_eur),
        purchase_date=data.get("purchase_date") or utcnow(),
        purchase_shipping_eur=data.get("purchase_shipping_eur") or 0,
        repair_cost_eur=data.get("repair_cost_eur") or 0,
        authentication_cost_eur=data.get("authentication_cost_eur") or 0,
        other_purchase_cost_eur=data.get("other_purchase_cost_eur") or 0,
        expected_sale_price_eur=data.get("expected_sale_price_eur") or opp.quick_sale_eur,
        notes=data.get("notes") or "",
    )
    deal.expected_profit_eur = round((deal.expected_sale_price_eur or 0) - total_cost(deal) - (opp.sell_costs_eur or 0), 2)
    session.add(deal)
    session.flush()
    log_status(session, "deal", deal.id, None, "PURCHASED", "created from opportunity")
    return deal


def set_deal_status(session: Session, deal: Deal, new: str, data: dict[str, Any] | None = None) -> Deal:
    data = data or {}
    new = DealStatus(new).value
    old = deal.status
    if new != old and new not in ALLOWED_TRANSITIONS.get(old, set()):
        raise TransitionError(f"cannot move deal from {old} to {new}")
    if new == "SOLD":
        if data.get("sale_price_eur") is None and deal.sale_price_eur is None:
            raise TransitionError("sale_price_eur is required to mark a deal as SOLD")
        for f in ("sale_price_eur", "sale_marketplace", "sale_date", "sale_fees_eur", "sale_shipping_eur", "sale_other_costs_eur"):
            if data.get(f) is not None:
                setattr(deal, f, data[f])
        deal.sale_date = deal.sale_date or utcnow()
    deal.status = new
    if new != old:
        log_status(session, "deal", deal.id, old, new, data.get("note", ""))
    if deal.opportunity_id:
        opp = session.get(Opportunity, deal.opportunity_id)
        if opp and opp.status != new:
            opp.status = new
            opp.is_active = False
    return deal


# ---------------------------------------------------------------------------- metrics


def total_cost(d: Deal) -> float:
    return float(
        (d.purchase_price_eur or 0) + (d.purchase_shipping_eur or 0) + (d.repair_cost_eur or 0)
        + (d.authentication_cost_eur or 0) + (d.other_purchase_cost_eur or 0)
    )


@dataclass
class DealMetrics:
    total_cost: float
    proceeds: float | None
    profit: float | None
    roi: float | None
    holding_days: float | None
    annualized_return: float | None


def deal_metrics(d: Deal, now: datetime | None = None) -> DealMetrics:
    now = now or utcnow()
    cost = total_cost(d)
    start = _aware(d.purchase_date)
    if d.status == "SOLD" and d.sale_price_eur is not None:
        proceeds = float(d.sale_price_eur) - float(d.sale_fees_eur or 0) - float(d.sale_shipping_eur or 0) - float(d.sale_other_costs_eur or 0)
        profit = proceeds - cost
        end = _aware(d.sale_date) or now
        days = max(1.0, (end - start).total_seconds() / 86400) if start else None
        roi = profit / cost if cost else None
        ann = (roi * 365 / days) if (roi is not None and days) else None
        return DealMetrics(round(cost, 2), round(proceeds, 2), round(profit, 2), roi, days, ann)
    days = max(0.0, (now - start).total_seconds() / 86400) if start else None
    return DealMetrics(round(cost, 2), None, None, None, days, None)


def portfolio_summary(session: Session, now: datetime | None = None) -> dict[str, Any]:
    now = now or utcnow()
    deals = list(session.scalars(select(Deal)))
    inventory = [d for d in deals if d.status in {s.value for s in INVENTORY_STATUSES}]
    sold = [d for d in deals if d.status == "SOLD"]
    inv_cost = sum(total_cost(d) for d in inventory)
    inv_value = sum(float(d.expected_sale_price_eur or total_cost(d)) for d in inventory)
    unrealized = sum(float(d.expected_profit_eur or 0) for d in inventory)

    realized, rois, holds, capital_days = 0.0, [], [], 0.0
    monthly: dict[str, float] = defaultdict(float)
    by_cat: dict[str, dict[str, float]] = defaultdict(lambda: {"profit": 0.0, "n": 0, "cost": 0.0})
    by_mp: dict[str, dict[str, float]] = defaultdict(lambda: {"profit": 0.0, "n": 0, "cost": 0.0})
    by_country: dict[str, dict[str, float]] = defaultdict(lambda: {"profit": 0.0, "n": 0, "cost": 0.0})
    for d in sold:
        m = deal_metrics(d, now)
        if m.profit is None:
            continue
        realized += m.profit
        if m.roi is not None:
            rois.append(m.roi)
        if m.holding_days:
            holds.append(m.holding_days)
            capital_days += m.total_cost * m.holding_days
        sale_date = _aware(d.sale_date) or now
        monthly[sale_date.strftime("%Y-%m")] += m.profit
        for bucket, key in ((by_cat, d.category_code or "other"), (by_mp, d.source_marketplace or "other"), (by_country, d.source_country or "?")):
            bucket[key]["profit"] += m.profit
            bucket[key]["n"] += 1
            bucket[key]["cost"] += m.total_cost

    aging = {"0_30": 0, "30_60": 0, "60_90": 0, "90_plus": 0}
    aging_value = {"0_30": 0.0, "30_60": 0.0, "60_90": 0.0, "90_plus": 0.0}
    for d in inventory:
        days = deal_metrics(d, now).holding_days or 0
        key = "0_30" if days < 30 else "30_60" if days < 60 else "60_90" if days < 90 else "90_plus"
        aging[key] += 1
        aging_value[key] += total_cost(d)

    def _fmt(b: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
        return sorted(
            [{"key": k, "profit": round(v["profit"], 2), "n": int(v["n"]), "roi": round(v["profit"] / v["cost"], 4) if v["cost"] else None} for k, v in b.items()],
            key=lambda x: -x["profit"],
        )

    return {
        "capital_deployed": round(inv_cost, 2),
        "inventory_count": len(inventory),
        "inventory_acquisition_cost": round(inv_cost, 2),
        "estimated_inventory_value": round(inv_value, 2),
        "unrealized_expected_profit": round(unrealized, 2),
        "realized_profit": round(realized, 2),
        "deals_sold": len(sold),
        "average_roi": round(sum(rois) / len(rois), 4) if rois else None,
        "average_holding_days": round(sum(holds) / len(holds), 1) if holds else None,
        # capital-weighted annualised return: profit per EUR-day of capital, x365
        "annualized_return_on_capital": round(realized / capital_days * 365, 4) if capital_days else None,
        "monthly_realized_profit": [{"month": k, "profit": round(v, 2)} for k, v in sorted(monthly.items())],
        "profit_by_category": _fmt(by_cat),
        "profit_by_marketplace": _fmt(by_mp),
        "profit_by_country": _fmt(by_country),
        "inventory_aging": aging,
        "inventory_aging_value": {k: round(v, 2) for k, v in aging_value.items()},
    }
