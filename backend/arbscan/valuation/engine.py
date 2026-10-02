"""Market value engine.

Turns a set of comparable listings into a price distribution and value estimates.
It is deliberately *not* a plain average:

* comparables whose critical attributes differ (e.g. yellow vs white gold) are excluded,
  minor attribute mismatches (size, colour) are down-weighted;
* every price is condition-normalised to a "good" baseline, then re-scaled to the target;
* completed (sold) transactions weigh ``sold_weight`` times more than asking prices,
  and asking prices are discounted (``ask_to_sale``) because asks overstate sale prices;
* stale asks (long time on market) are down-weighted - they are evidence of *over*pricing;
* comparables from the resale market weigh more than other countries;
* outliers are removed with a robust (MAD) z-score on log prices.

All knobs live in :class:`ValuationConfig` and can be overridden from app settings.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from arbscan.db.enums import ConfidenceLevel
from arbscan.normalization.dictionaries import CONDITION_FACTORS
from arbscan.valuation.stats import (
    robust_outlier_mask,
    weighted_median,
    weighted_quantile,
    weighted_trimmed_mean,
)


@dataclass
class ValuationConfig:
    sold_weight: float = 3.0
    ended_weight: float = 1.5  # listing disappeared (probable sale) - better evidence than a live ask
    ask_to_sale: float = 0.93  # expected transaction price / asking price
    other_country_weight: float = 0.5
    professional_seller_weight: float = 0.8
    stale_ask_days: float = 60
    stale_ask_weight: float = 0.6
    very_stale_ask_days: float = 120
    very_stale_ask_weight: float = 0.35
    old_sold_days: float = 180
    old_sold_weight: float = 0.5
    unknown_critical_weight: float = 0.6
    outlier_z: float = 3.0
    quick_sale_quantile: float = 0.35
    quick_sale_sold_factor: float = 0.95
    opportunistic_margin: float = 0.30
    min_comparables: int = 3
    accessory_premiums: dict[str, float] = field(default_factory=lambda: {"box": 0.03, "papers": 0.06})


@dataclass
class Comparable:
    price_eur: float
    kind: str = "asking"  # asking | ended (left the market, outcome unknown) | sold
    condition: str = "unknown"
    country: str = "ES"
    attributes: dict[str, str] = field(default_factory=dict)
    observed_at: datetime | None = None
    days_on_market: float | None = None
    seller_type: str | None = None
    accessories: dict[str, bool] = field(default_factory=dict)
    is_active: bool = True
    listing_id: int | None = None
    marketplace: str | None = None


@dataclass
class ValuationResult:
    n_comparables: int = 0
    n_sold: int = 0
    n_outliers: int = 0
    n_excluded: int = 0
    effective_n: float = 0.0
    median_eur: float | None = None
    trimmed_mean_eur: float | None = None
    p25_eur: float | None = None
    p75_eur: float | None = None
    lowest_reasonable_eur: float | None = None
    quick_sale_eur: float | None = None
    market_value_eur: float | None = None
    opportunistic_buy_eur: float | None = None
    dispersion: float | None = None
    confidence_score: float = 0.0
    confidence_level: str = ConfidenceLevel.INSUFFICIENT.value
    median_days_on_market: float | None = None
    by_country: dict[str, dict[str, float]] = field(default_factory=dict)
    by_marketplace: dict[str, dict[str, float]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    used_listing_ids: list[int] = field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        return self.market_value_eur is not None and self.confidence_level != ConfidenceLevel.INSUFFICIENT.value

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["used_listing_ids"] = self.used_listing_ids[:200]
        return d


def _accessory_factor(acc: dict[str, bool], premiums: dict[str, float]) -> float:
    return 1.0 + sum(p for k, p in premiums.items() if acc.get(k))


def _r(x: float | None) -> float | None:
    return None if x is None else round(x, 2)


class ValuationEngine:
    def __init__(self, config: ValuationConfig | None = None):
        self.config = config or ValuationConfig()

    def comparable_weight(
        self,
        comp: Comparable,
        *,
        target_attrs: dict[str, str],
        variant_importance: dict[str, float],
        market: str,
        now: datetime,
    ) -> float:
        """0 = excluded. Otherwise a positive weight."""
        c = self.config
        w = 1.0
        for attr, importance in variant_importance.items():
            importance = float(importance)
            tv, cv = target_attrs.get(attr), comp.attributes.get(attr)
            if tv is None and cv is None:
                continue
            if tv is not None and cv is not None:
                if str(tv).lower() != str(cv).lower():
                    if importance >= 0.8:
                        return 0.0
                    w *= max(0.1, 1 - importance)
            else:
                # one side unknown
                w *= c.unknown_critical_weight if importance >= 0.8 else (1 - importance * 0.3)
        if comp.kind == "sold":
            w *= c.sold_weight
            if comp.observed_at:
                age = (now - comp.observed_at).total_seconds() / 86400
                if age > c.old_sold_days:
                    w *= c.old_sold_weight
        elif comp.kind == "ended":
            w *= c.ended_weight
            if comp.days_on_market is not None and comp.days_on_market > c.stale_ask_days:
                w *= c.stale_ask_weight  # probably withdrawn rather than sold
        else:
            dom = comp.days_on_market
            if dom is not None:
                if dom > c.very_stale_ask_days:
                    w *= c.very_stale_ask_weight
                elif dom > c.stale_ask_days:
                    w *= c.stale_ask_weight
        if market not in ("EU", comp.country):
            w *= c.other_country_weight
        if comp.seller_type == "professional":
            w *= c.professional_seller_weight
        return w

    def value(
        self,
        comparables: list[Comparable],
        *,
        target_attrs: dict[str, str] | None = None,
        variant_importance: dict[str, float] | None = None,
        market: str = "ES",
        target_condition: str = "good",
        target_accessories: dict[str, bool] | None = None,
        exclude_listing_id: int | None = None,
        apply_accessory_premiums: bool = False,
        now: datetime | None = None,
    ) -> ValuationResult:
        c = self.config
        now = now or datetime.now(UTC)
        target_attrs = target_attrs or {}
        variant_importance = variant_importance or {}
        res = ValuationResult()

        prices: list[float] = []
        weights: list[float] = []
        used: list[Comparable] = []
        for comp in comparables:
            if exclude_listing_id is not None and comp.listing_id == exclude_listing_id:
                continue
            if not comp.price_eur or comp.price_eur <= 0:
                continue
            if comp.condition == "for_parts" and target_condition != "for_parts":
                res.n_excluded += 1
                continue
            w = self.comparable_weight(
                comp, target_attrs=target_attrs, variant_importance=variant_importance, market=market, now=now
            )
            if w <= 0:
                res.n_excluded += 1
                continue
            # normalise to transaction-equivalent, "good" condition, no accessories
            p = comp.price_eur * (1.0 if comp.kind == "sold" else c.ask_to_sale)
            p /= CONDITION_FACTORS.get(comp.condition, 1.0)
            if apply_accessory_premiums:
                p /= _accessory_factor(comp.accessories, c.accessory_premiums)
            prices.append(p)
            weights.append(w)
            used.append(comp)

        if not prices:
            res.notes.append("no comparable listings")
            return res

        keep = robust_outlier_mask(prices, c.outlier_z)
        res.n_outliers = sum(1 for k in keep if not k)
        prices = [p for p, k in zip(prices, keep, strict=True) if k]
        weights = [w for w, k in zip(weights, keep, strict=True) if k]
        used = [u for u, k in zip(used, keep, strict=True) if k]
        res.n_comparables = len(used)
        res.n_sold = sum(1 for u in used if u.kind == "sold")
        res.used_listing_ids = [u.listing_id for u in used if u.listing_id is not None]
        # effective sample size (Kish) - robust to a few heavy weights
        res.effective_n = round(sum(weights) ** 2 / sum(w * w for w in weights), 2)

        # re-scale to the target's condition / accessories
        scale = CONDITION_FACTORS.get(target_condition, 1.0)
        if apply_accessory_premiums:
            scale *= _accessory_factor(target_accessories or {}, c.accessory_premiums)

        median = weighted_median(prices, weights) * scale
        res.median_eur = _r(median)
        res.trimmed_mean_eur = _r(weighted_trimmed_mean(prices, weights) * scale)
        p10 = weighted_quantile(prices, weights, 0.10) * scale
        p25 = weighted_quantile(prices, weights, 0.25) * scale
        p75 = weighted_quantile(prices, weights, 0.75) * scale
        res.p25_eur, res.p75_eur, res.lowest_reasonable_eur = _r(p25), _r(p75), _r(p10)
        res.market_value_eur = _r(median)

        quick = weighted_quantile(prices, weights, c.quick_sale_quantile) * scale
        sold_prices = [(p, w) for p, w, u in zip(prices, weights, used, strict=True) if u.kind == "sold"]
        if sold_prices:
            sold_median = weighted_median([p for p, _ in sold_prices], [w for _, w in sold_prices]) * scale
            quick = min(quick, sold_median * c.quick_sale_sold_factor)
        res.quick_sale_eur = _r(min(quick, median))
        res.opportunistic_buy_eur = _r(res.quick_sale_eur * (1 - c.opportunistic_margin))
        res.dispersion = round((p75 - p25) / median, 4) if median else None

        doms = [u.days_on_market for u in used if not u.is_active and u.days_on_market is not None]
        if doms:
            doms.sort()
            res.median_days_on_market = round(doms[len(doms) // 2], 1)

        self._breakdowns(res, used, prices, scale)
        self._confidence(res)
        return res

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _breakdowns(res: ValuationResult, used: list[Comparable], prices: list[float], scale: float) -> None:
        by_c: dict[str, list[float]] = {}
        by_m: dict[str, list[float]] = {}
        for u, p in zip(used, prices, strict=True):
            by_c.setdefault(u.country, []).append(p * scale)
            if u.marketplace:
                by_m.setdefault(u.marketplace, []).append(p * scale)
        for target, src in ((res.by_country, by_c), (res.by_marketplace, by_m)):
            for k, vals in src.items():
                vals.sort()
                target[k] = {"n": len(vals), "median": round(vals[len(vals) // 2], 2), "min": round(vals[0], 2)}

    def _confidence(self, res: ValuationResult) -> None:
        import math

        n = res.n_comparables
        if n < self.config.min_comparables:
            res.confidence_score = round(0.1 * n, 2)
            res.confidence_level = ConfidenceLevel.INSUFFICIENT.value
            res.notes.append(f"only {n} comparable(s) - estimate not reliable")
            return
        n_factor = 1 - math.exp(-res.effective_n / 7)
        disp = res.dispersion or 0
        disp_factor = max(0.3, min(1.0, 1 - max(0.0, disp - 0.15) / 0.6))
        sold_bonus = 0.12 * min(1.0, res.n_sold / 5)
        score = min(0.99, 0.85 * n_factor * disp_factor + sold_bonus)
        res.confidence_score = round(score, 3)
        if score >= 0.7 and n >= 10:
            level = ConfidenceLevel.HIGH
        elif score >= 0.45 and n >= 5:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
        res.confidence_level = level.value
        if disp > 0.45:
            res.notes.append(f"wide price dispersion ({disp:.0%} IQR/median)")
        if res.n_sold == 0:
            res.notes.append("no completed-sale data; based on asking prices (discounted)")
