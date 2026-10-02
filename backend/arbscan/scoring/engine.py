"""Opportunity scoring, liquidity & capital-velocity metrics, opportunity classification.

Design principle: optimise NET PROFIT x CAPITAL VELOCITY, not discount %.
Every component is returned separately (0-100) together with the final score, and all
weights/scales live in :class:`ScoringConfig` (editable in Settings).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

from arbscan.db.enums import ConfidenceLevel, OpportunityType, RiskLevel


@dataclass
class ScoringConfig:
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "discount": 0.13,
            "profit": 0.24,
            "roi": 0.15,
            "liquidity": 0.13,
            "freshness": 0.08,
            "confidence": 0.12,
            "velocity": 0.15,
        }
    )
    risk_penalty_weight: float = 0.35
    discount_full_score: float = 0.40  # 40 % below market -> 100
    profit_scale_eur: float = 350.0  # 1 - exp(-profit/scale)
    roi_full_score: float = 0.45
    annualized_roi_full_score: float = 4.0  # 400 % annualised -> 100 (log-scaled)
    freshness_half_life_hours: float = 72.0
    cap_insufficient_confidence: float = 35.0
    cap_low_confidence: float = 72.0
    cap_high_risk: float = 60.0
    cap_unprofitable: float = 25.0
    negotiation_success_factor: float = 0.75
    # negotiation opportunity detection
    negotiation_min_age_days: float = 21.0
    negotiation_max_premium_over_market: float = 0.30
    negotiation_base_discount: float = 0.05
    negotiation_discount_per_day: float = 0.0025
    negotiation_discount_per_drop: float = 0.03
    negotiation_max_discount: float = 0.30
    # liquidity
    liquidity_high: float = 67.0
    liquidity_medium: float = 40.0
    transit_days: dict[str, float] = field(default_factory=lambda: {"domestic": 3, "intra_eu": 7, "import": 14})
    authentication_days: float = 4.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ScoringConfig:
        cfg = cls()
        for k, v in (data or {}).items():
            if hasattr(cfg, k):
                if k == "weights" and isinstance(v, dict):
                    cfg.weights.update({kk: float(vv) for kk, vv in v.items()})
                else:
                    setattr(cfg, k, v)
        return cfg

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------- liquidity
@dataclass
class LiquidityInput:
    n_active_comparables: int = 0
    n_sold_recent: int = 0  # completed sales (or listings that ended) in the last 30 days
    median_days_on_market: float | None = None
    popularity: float = 0.5
    base_holding_days: float = 21.0


@dataclass
class LiquidityResult:
    score: float
    label: str
    expected_holding_days_quick: float
    expected_holding_days_market: float
    signals: dict[str, float]


def estimate_liquidity(i: LiquidityInput, cfg: ScoringConfig | None = None) -> LiquidityResult:
    cfg = cfg or ScoringConfig()
    supply = min(1.0, i.n_active_comparables / 25)
    demand = min(1.0, i.n_sold_recent / 10)
    if i.median_days_on_market is not None:
        dom = max(1.0, i.median_days_on_market)
        turnover = max(0.0, min(1.0, 1 - math.log(dom / 7) / math.log(90 / 7))) if dom > 7 else 1.0
        score = 100 * (0.30 * i.popularity + 0.15 * supply + 0.25 * demand + 0.30 * turnover)
        base_days = 0.5 * i.base_holding_days + 0.5 * dom
    else:
        turnover = None
        score = 100 * (0.55 * i.popularity + 0.25 * supply + 0.20 * demand)
        base_days = i.base_holding_days
    score = round(max(0.0, min(100.0, score)), 1)
    label = "High" if score >= cfg.liquidity_high else "Medium" if score >= cfg.liquidity_medium else "Low"
    liquidity_factor = 1.5 - score / 100  # 0.5 (very liquid) .. 1.5 (illiquid)
    market_days = max(2.0, base_days * liquidity_factor)
    return LiquidityResult(
        score=score,
        label=label,
        expected_holding_days_quick=round(max(1.0, market_days * 0.55), 1),
        expected_holding_days_market=round(market_days, 1),
        signals={
            "supply": round(supply, 3),
            "demand": round(demand, 3),
            "turnover": round(turnover, 3) if turnover is not None else -1,
            "popularity": i.popularity,
        },
    )


# ---------------------------------------------------------------------------- velocity
@dataclass
class VelocityMetrics:
    holding_days: float
    holding_period_roi: float
    annualized_roi: float
    profit_velocity: float  # EUR per day
    capital_efficiency: float  # profit / capital / day
    profit_per_1000: float
    capital_turnover_per_year: float


def velocity_metrics(net_profit: float, capital: float, holding_days: float) -> VelocityMetrics:
    days = max(1.0, holding_days)
    roi = net_profit / capital if capital > 0 else 0.0
    # compound annualisation is unstable for very short holds; use simple annualisation, capped
    annualized = max(-1.0, min(roi * 365 / days, 50.0))
    return VelocityMetrics(
        holding_days=round(days, 1),
        holding_period_roi=round(roi, 4),
        annualized_roi=round(annualized, 4),
        profit_velocity=round(net_profit / days, 2),
        capital_efficiency=round(roi / days, 6),
        profit_per_1000=round(1000 * roi, 2),
        capital_turnover_per_year=round(365 / days, 2),
    )


# ---------------------------------------------------------------------------- score
@dataclass
class ScoreInput:
    purchase_price: float
    market_value: float | None
    quick_sale: float | None
    net_profit: float | None
    roi: float | None
    liquidity_score: float
    listing_age_hours: float
    valuation_confidence_score: float
    valuation_confidence_level: str
    normalization_confidence: float
    risk_score: float
    risk_level: str
    annualized_roi: float | None
    opportunity_type: str = OpportunityType.FLIP.value


@dataclass
class ScoreResult:
    score: float
    components: dict[str, float]
    caps_applied: list[str]
    explanation: list[str]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_score(i: ScoreInput, cfg: ScoringConfig | None = None) -> ScoreResult:
    cfg = cfg or ScoringConfig()
    comp: dict[str, float] = {}
    expl: list[str] = []

    discount = 1 - i.purchase_price / i.market_value if i.market_value else 0.0
    comp["discount"] = 100 * _clamp01(discount / cfg.discount_full_score)
    profit = i.net_profit or 0.0
    comp["profit"] = 100 * (1 - math.exp(-profit / cfg.profit_scale_eur)) if profit > 0 else 0.0
    comp["roi"] = 100 * _clamp01((i.roi or 0) / cfg.roi_full_score)
    comp["liquidity"] = i.liquidity_score
    comp["freshness"] = 100 * 0.5 ** (max(0.0, i.listing_age_hours) / cfg.freshness_half_life_hours)
    comp["confidence"] = 100 * (0.6 * i.valuation_confidence_score + 0.4 * i.normalization_confidence)
    ann = i.annualized_roi or 0.0
    comp["velocity"] = 100 * _clamp01(math.log1p(max(0.0, ann)) / math.log1p(cfg.annualized_roi_full_score))

    wsum = sum(cfg.weights.values()) or 1.0
    positive = sum(comp[k] * w for k, w in cfg.weights.items() if k in comp) / wsum
    penalty = i.risk_score * cfg.risk_penalty_weight
    comp["risk_penalty"] = -penalty
    score = positive - penalty

    caps: list[str] = []
    if i.opportunity_type == OpportunityType.NEGOTIATION.value:
        score *= cfg.negotiation_success_factor
        caps.append(f"negotiation x{cfg.negotiation_success_factor}")
    if profit <= 0:
        score = min(score, cfg.cap_unprofitable)
        caps.append("not profitable at this price")
    if i.valuation_confidence_level == ConfidenceLevel.INSUFFICIENT.value:
        score = min(score, cfg.cap_insufficient_confidence)
        caps.append("insufficient market data")
    elif i.valuation_confidence_level == ConfidenceLevel.LOW.value:
        score = min(score, cfg.cap_low_confidence)
        caps.append("low valuation confidence")
    if i.risk_level == RiskLevel.HIGH.value:
        score = min(score, cfg.cap_high_risk)
        caps.append("high risk")

    for k in ("profit", "roi", "velocity", "liquidity", "discount"):
        if comp[k] >= 75:
            expl.append(f"strong {k}")
    comp = {k: round(v, 1) for k, v in comp.items()}
    return ScoreResult(round(max(0.0, min(100.0, score)), 1), comp, caps, expl)


# ---------------------------------------------------------------------------- negotiation
def achievable_discount(age_days: float, price_drops: int, cfg: ScoringConfig | None = None) -> float:
    """Heuristic: how much below ask an old listing can typically be bought for."""
    cfg = cfg or ScoringConfig()
    d = cfg.negotiation_base_discount + cfg.negotiation_discount_per_day * age_days + cfg.negotiation_discount_per_drop * price_drops
    return round(min(cfg.negotiation_max_discount, d), 4)


def nice_round(price: float) -> float:
    """Round offers down to human numbers (e.g. 2,987 -> 2,980; 1,148 -> 1,140; 437 -> 435)."""
    if price <= 0:
        return 0.0
    step = 50 if price >= 5000 else 10 if price >= 300 else 5 if price >= 50 else 1
    return float(math.floor(price / step) * step)


def classify_opportunity(
    *,
    asking: float,
    max_buy_price: float,
    market_value: float | None,
    net_profit_at_ask: float | None,
    roi_at_ask: float | None,
    min_roi: float,
    source_country: str,
    resale_country: str,
    listing_age_days: float,
    price_drops: int,
    cfg: ScoringConfig | None = None,
) -> tuple[str, float | None, str]:
    """Return (type, target_offer, reason)."""
    cfg = cfg or ScoringConfig()
    if market_value is None:
        return OpportunityType.NONE.value, None, "no market value"
    if net_profit_at_ask is not None and net_profit_at_ask > 0 and (roi_at_ask or 0) >= min_roi:
        kind = OpportunityType.FLIP if source_country == resale_country else OpportunityType.CROSS_BORDER
        return kind.value, None, "profitable at asking price"
    if max_buy_price <= 0:
        return OpportunityType.NONE.value, None, "no profitable purchase price"
    if asking > market_value * (1 + cfg.negotiation_max_premium_over_market):
        return OpportunityType.NONE.value, None, "asking price far above market"
    required = 1 - max_buy_price / asking
    achievable = achievable_discount(listing_age_days, price_drops, cfg)
    old_enough = listing_age_days >= cfg.negotiation_min_age_days or price_drops > 0
    if old_enough and required <= achievable * 1.5:
        target = nice_round(max_buy_price * 0.97)
        return OpportunityType.NEGOTIATION.value, target, (
            f"needs {required:.0%} off ask; listing {listing_age_days:.0f} days old "
            f"(typical achievable ~{achievable:.0%})"
        )
    return OpportunityType.NONE.value, None, f"needs {required:.0%} off ask"
