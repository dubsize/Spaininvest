"""Alert rule evaluation, message formatting and de-duplicated dispatch.

De-duplication: an alert is sent at most once per (listing, channel, fingerprint).
The fingerprint changes only when the price or opportunity type changes, so an
unchanged listing never re-alerts; a price reduction produces a new fingerprint and
(if the rule allows price drops) a new alert.
"""

from __future__ import annotations

import operator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from arbscan.alerts.channels import AlertMessage, Channel, available_channels
from arbscan.core.config import get_settings
from arbscan.core.logging import get_logger
from arbscan.db.models import AlertEvent, AlertRule, Listing, Opportunity
from arbscan.risk.engine import AUTH_WARNING

log = get_logger(__name__)

OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq, "!=": operator.ne}
RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

DEFAULT_RULES: list[dict[str, Any]] = [
    {
        "name": "Default deal alert",
        "conditions": {
            "any": [
                {"all": [{"field": "score", "op": ">=", "value": 80}]},
                {"all": [{"field": "net_profit", "op": ">=", "value": 250}, {"field": "roi", "op": ">=", "value": 0.20}]},
                {"all": [{"field": "price_to_quick_sale", "op": "<=", "value": 0.70}]},
            ]
        },
        "channels": ["telegram", "email", "log"],
        "include_price_drops": True,
        "max_risk_level": "HIGH",
    }
]


def opportunity_fields(opp: Opportunity) -> dict[str, float | None]:
    profit = opp.net_profit_quick_eur
    if opp.opportunity_type == "NEGOTIATION":
        profit = opp.profit_at_target_offer_eur
    return {
        "score": opp.score,
        "net_profit": profit,
        "roi": opp.roi,
        "discount": opp.discount_pct,
        "price": opp.purchase_price_eur,
        "price_to_quick_sale": (opp.purchase_price_eur / opp.quick_sale_eur) if opp.quick_sale_eur else None,
        "liquidity": opp.liquidity_score,
        "annualized_roi": opp.annualized_roi,
        "confidence": opp.confidence_score,
        "risk_score": opp.risk_score,
    }


def _clause_ok(clause: dict[str, Any], values: dict[str, float | None]) -> bool:
    v = values.get(clause.get("field", ""))
    op = OPS.get(clause.get("op", ">="))
    if v is None or op is None:
        return False
    return bool(op(v, clause.get("value")))


def rule_matches(conditions: dict[str, Any], values: dict[str, float | None]) -> bool:
    groups = conditions.get("any") or []
    if not groups and conditions.get("all"):
        groups = [{"all": conditions["all"]}]
    return any(all(_clause_ok(c, values) for c in g.get("all", [])) for g in groups)


def _eur(v: float | None) -> str:
    return "n/a" if v is None else f"€{v:,.0f}"


def _age(listing: Listing, now: datetime) -> str:
    start = listing.published_at or listing.first_seen_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    mins = max(0, int((now - start).total_seconds() // 60))
    if mins < 60:
        return f"{mins} min"
    if mins < 60 * 48:
        return f"{mins // 60} h"
    return f"{mins // 1440} days"


def format_alert(opp: Opportunity, listing: Listing, kind: str = "deal", now: datetime | None = None) -> AlertMessage:
    now = now or datetime.now(UTC)
    product = opp.canonical_product.name if opp.canonical_product else listing.title
    variant = " — ".join(v.replace("_", " ").title() for v in (listing.variant or {}).values())
    header = "🔥 DEAL ALERT" if kind == "deal" else "📉 PRICE DROP"
    if opp.opportunity_type == "NEGOTIATION":
        header = "🤝 NEGOTIATION OPPORTUNITY" if kind == "deal" else header
    lines = [header, "", f"{product}{' — ' + variant if variant else ''}", ""]
    lines.append(f"Marketplace: {listing.marketplace.name if listing.marketplace else listing.marketplace_code}")
    lines.append(f"Location: {listing.city or '?'} ({listing.country})")
    lines.append(f"Price: {_eur(opp.purchase_price_eur)}")
    if kind == "price_drop" and listing.last_price_change_pct is not None:
        lines.append(f"Price change: {listing.last_price_change_pct:+.1%} (reduction #{listing.price_drop_count})")
    if opp.opportunity_type == "CROSS_BORDER":
        lines.append(f"Type: cross-border {opp.source_country} → {opp.resale_country}")
    lines += ["", f"Estimated quick-sale: {_eur(opp.quick_sale_eur)}", f"Estimated market value: {_eur(opp.market_value_eur)}", ""]
    if opp.opportunity_type == "NEGOTIATION":
        lines.append(f"Target offer: {_eur(opp.target_offer_eur)} (max buy {_eur(opp.max_buy_price_eur)})")
        lines.append(f"Expected profit at target offer: {_eur(opp.profit_at_target_offer_eur)}")
    else:
        lines.append(f"Estimated net profit: {_eur(opp.net_profit_quick_eur)}")
        lines.append(f"ROI: {(opp.roi or 0):.1%}")
    lines += ["", f"Discount to market: {(opp.discount_pct or 0):.1%}", f"Listing age: {_age(listing, now)}", ""]
    lines.append(f"Risk: {opp.risk_level}")
    reasons = [f["message"] for f in (opp.risk_flags or []) if f.get("points", 0) > 0][:4]
    positives = [f["message"] for f in (opp.risk_flags or []) if f.get("points", 0) <= 0][:2]
    if reasons or positives:
        lines.append("Reason:")
        lines += [f"* {r}" for r in reasons + positives]
    if opp.requires_authentication:
        lines += ["", AUTH_WARNING]
    lines += ["", f"Confidence: {opp.confidence_level} ({(opp.score_components or {}).get('valuation', {}).get('n', 0)} comparables)"]
    lines += ["", f"Opportunity Score: {opp.score:.0f}/100", "", f"[OPEN LISTING] {listing.url}"]
    web = get_settings().public_web_url.rstrip("/")
    lines.append(f"[ANALYSIS] {web}/listings/{listing.id}")
    subject = f"{header.split(' ', 1)[1]}: {product} {_eur(opp.purchase_price_eur)} (score {opp.score:.0f})"
    return AlertMessage(subject=subject, text="\n".join(lines), url=listing.url)


def ensure_default_rules(session: Session) -> None:
    if session.scalars(select(AlertRule).limit(1)).first() is None:
        for r in DEFAULT_RULES:
            session.add(AlertRule(**r))
        session.flush()


class AlertDispatcher:
    def __init__(self, session: Session, channels: dict[str, Channel] | None = None, now: datetime | None = None):
        self.session = session
        self.channels = channels if channels is not None else available_channels()
        self.now = now or datetime.now(UTC)
        self.rules = [r for r in session.scalars(select(AlertRule).where(AlertRule.enabled.is_(True)))]

    def process(self, opp: Opportunity, *, price_dropped: bool = False, dry_run: bool = False) -> int:
        """Evaluate rules for one opportunity and send de-duplicated alerts. Returns #sent."""
        if not opp.is_active or opp.status in ("REJECTED", "SCAM_RISK", "EXPIRED", "SOLD"):
            return 0
        listing = opp.listing
        values = opportunity_fields(opp)
        sent = 0
        for rule in self.rules:
            if RISK_ORDER.get(opp.risk_level, 0) > RISK_ORDER.get(rule.max_risk_level, 2):
                continue
            if not rule_matches(rule.conditions or {}, values):
                continue
            kind = "price_drop" if price_dropped and rule.include_price_drops else "deal"
            msg = format_alert(opp, listing, kind, self.now)
            channels = rule.channels or ["log"]
            if listing.is_demo:
                channels = ["log"]  # demo data never reaches Telegram / e-mail
            for ch_name in channels:
                ch = self.channels.get(ch_name)
                if ch is None or not ch.is_configured():
                    continue
                if self._already_sent(listing.id, ch_name, opp.fingerprint):
                    continue
                event = AlertEvent(
                    listing_id=listing.id, opportunity_id=opp.id, rule_id=rule.id, channel=ch_name,
                    kind=kind, fingerprint=opp.fingerprint, message=msg.text, created_at=self.now,
                )
                try:
                    with self.session.begin_nested():
                        self.session.add(event)
                        self.session.flush()
                except IntegrityError:
                    continue  # raced with another worker - already alerted
                if dry_run:
                    event.status = "skipped"
                    continue
                try:
                    ch.send(msg)
                    event.status = "sent"
                    sent += 1
                except Exception as exc:  # noqa: BLE001
                    event.status = "failed"
                    event.error = str(exc)[:500]
                    log.warning("alert send failed", extra={"channel": ch_name, "err": str(exc)})
        return sent

    def _already_sent(self, listing_id: int, channel: str, fingerprint: str) -> bool:
        return (
            self.session.scalar(
                select(AlertEvent.id).where(
                    AlertEvent.listing_id == listing_id, AlertEvent.channel == channel, AlertEvent.fingerprint == fingerprint
                )
            )
            is not None
        )
