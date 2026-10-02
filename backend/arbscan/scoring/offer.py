"""'WHAT SHOULD I OFFER?' calculator."""

from __future__ import annotations

from dataclasses import dataclass

from arbscan.fees.engine import FeeEngine, TradeContext
from arbscan.scoring.engine import achievable_discount, nice_round


@dataclass
class OfferInput:
    asking_price: float
    expected_resale: float
    target_roi: float
    target_profit_eur: float = 0.0
    expected_costs_eur: float | None = None  # override: fixed total costs instead of fee engine
    listing_age_days: float = 0.0
    price_drops: int = 0


@dataclass
class OfferResult:
    asking_price: float
    ideal_offer: float
    max_acceptable_offer: float
    expected_resale: float
    expected_costs: float
    expected_profit_at_ideal: float
    expected_roi_at_ideal: float
    expected_profit_at_max: float
    expected_profit_at_ask: float
    roi_at_ask: float
    deal_at_ask: bool
    negotiation_needed_pct: float
    note: str


def _simple_max(resale: float, costs: float, roi: float, min_profit: float) -> float:
    # profit = resale - costs - P ; ROI = profit / P  (costs treated as sale-side)
    by_roi = (resale - costs) / (1 + roi)
    by_profit = resale - costs - min_profit
    return max(0.0, min(by_roi, by_profit))


def calculate_offer(i: OfferInput, fee_engine: FeeEngine | None = None, ctx: TradeContext | None = None) -> OfferResult:
    if i.expected_costs_eur is not None or fee_engine is None or ctx is None:
        costs_at = lambda p: float(i.expected_costs_eur or 0.0)  # noqa: E731
        max_ok = _simple_max(i.expected_resale, costs_at(0), i.target_roi, i.target_profit_eur)

        def econ(p: float) -> tuple[float, float]:
            profit = i.expected_resale - costs_at(p) - p
            return profit, (profit / p if p else 0.0)
    else:
        max_ok = fee_engine.max_buy_price(
            i.expected_resale, ctx, target_roi=i.target_roi, min_profit_eur=i.target_profit_eur
        )

        def econ(p: float) -> tuple[float, float]:
            e = fee_engine.economics(p, i.expected_resale, ctx)
            return e.net_profit, e.roi

        def costs_at(p: float) -> float:
            return fee_engine.economics(p, i.expected_resale, ctx).total_costs

    max_acceptable = nice_round(max_ok)
    buffer = 0.04 + achievable_discount(i.listing_age_days, i.price_drops) * 0.5
    ideal = nice_round(min(max_acceptable * (1 - buffer), i.asking_price * (1 - buffer)))
    # don't open with an offer so low it ends the conversation (unless the maths requires it)
    floor = nice_round(i.asking_price * 0.70)
    if ideal < floor <= max_acceptable:
        ideal = floor
    ideal = min(ideal, max_acceptable)

    p_ideal, r_ideal = econ(ideal) if ideal > 0 else (0.0, 0.0)
    p_max, _ = econ(max_acceptable) if max_acceptable > 0 else (0.0, 0.0)
    p_ask, r_ask = econ(i.asking_price)
    needed = max(0.0, 1 - max_acceptable / i.asking_price) if i.asking_price else 0.0
    if max_acceptable <= 0:
        note = "No purchase price meets the target return at this resale estimate."
    elif i.asking_price <= max_acceptable:
        note = "Asking price already meets your target - offer slightly below ask or buy now."
    else:
        note = f"Needs {needed:.0%} off the asking price to meet your target."
    return OfferResult(
        asking_price=i.asking_price,
        ideal_offer=ideal,
        max_acceptable_offer=max_acceptable,
        expected_resale=i.expected_resale,
        expected_costs=round(costs_at(max_acceptable), 2),
        expected_profit_at_ideal=round(p_ideal, 2),
        expected_roi_at_ideal=round(r_ideal, 4),
        expected_profit_at_max=round(p_max, 2),
        expected_profit_at_ask=round(p_ask, 2),
        roi_at_ask=round(r_ask, 4),
        deal_at_ask=i.asking_price <= max_acceptable,
        negotiation_needed_pct=round(needed, 4),
        note=note,
    )
