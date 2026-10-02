"""Fee & cost engine.

Business logic never hard-codes fees: everything comes from :class:`FeeRuleData` /
:class:`CostProfileData` (loaded from the database, editable in the UI).

Definitions (used consistently across the app)
---------------------------------------------
* ``capital`` (total acquisition cost) = purchase price + buy-side costs
  (buyer fee, inbound shipping, insurance, import duty/VAT, misc) + preparation costs
  (authentication, refurbishment).
* ``net_profit`` = sale price - sell-side costs (selling fee, payment fee, outbound
  shipping, misc % of sale) - capital.
* ``roi`` = net_profit / capital.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_EU = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV",
    "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}


@dataclass
class FeeRuleData:
    side: str
    marketplace_code: str | None = None
    country: str | None = None
    category_code: str | None = None
    seller_type: str = "private"
    percent: float = 0.0
    fixed_eur: float = 0.0
    payment_percent: float = 0.0
    payment_fixed_eur: float = 0.0
    min_fee_eur: float | None = None
    max_fee_eur: float | None = None
    id: int | None = None

    def specificity(self) -> int:
        return (4 if self.marketplace_code else 0) + (2 if self.category_code else 0) + (1 if self.country else 0)

    def compute(self, amount: float) -> tuple[float, float]:
        fee = amount * self.percent + self.fixed_eur
        if self.min_fee_eur is not None:
            fee = max(fee, self.min_fee_eur)
        if self.max_fee_eur is not None:
            fee = min(fee, self.max_fee_eur)
        payment = amount * self.payment_percent + self.payment_fixed_eur
        return round(fee, 2), round(payment, 2)


@dataclass
class CostProfileData:
    route: str = "domestic"
    category_code: str | None = None
    shipping_class: str | None = None
    inbound_shipping_eur: float = 0.0
    outbound_shipping_eur: float = 0.0
    insurance_pct: float = 0.0
    import_duty_pct: float = 0.0
    import_vat_pct: float = 0.0
    misc_eur: float = 0.0
    misc_pct: float = 0.0
    travel_eur: float = 0.0
    name: str = ""
    id: int | None = None


@dataclass
class CategoryCosts:
    code: str
    shipping_class: str = "parcel_m"
    refurbishment_eur: float = 0.0
    authentication_eur: float = 0.0
    authentication_required: bool = False


@dataclass
class CostLine:
    label: str
    amount: float
    side: str  # buy | prep | sell
    note: str = ""


@dataclass
class CostBreakdown:
    lines: list[CostLine] = field(default_factory=list)

    def add(self, label: str, amount: float, side: str, note: str = "") -> None:
        if amount:
            self.lines.append(CostLine(label, round(amount, 2), side, note))

    def total(self, side: str | None = None) -> float:
        return round(sum(line.amount for line in self.lines if side is None or line.side == side), 2)

    def as_dict(self) -> dict[str, Any]:
        return {
            "lines": [line.__dict__ for line in self.lines],
            "buy": self.total("buy"),
            "prep": self.total("prep"),
            "sell": self.total("sell"),
            "total": self.total(),
        }


@dataclass
class TradeEconomics:
    purchase_price: float
    sale_price: float
    capital: float
    net_profit: float
    roi: float
    costs: CostBreakdown

    @property
    def total_costs(self) -> float:
        return self.costs.total()


@dataclass
class TradeContext:
    """Everything that determines the costs of a trade (excluding the prices)."""

    source_marketplace: str
    source_country: str
    resale_marketplace: str
    resale_country: str
    category: CategoryCosts
    listing_shipping_eur: float | None = None  # shipping cost published on the listing
    refurbishment_override_eur: float | None = None
    include_authentication: bool | None = None  # None -> category default
    local_pickup: bool = False
    extra_costs_eur: float = 0.0


class FeeEngine:
    def __init__(
        self,
        fee_rules: list[FeeRuleData],
        cost_profiles: list[CostProfileData],
        eu_countries: set[str] | None = None,
    ):
        self.fee_rules = fee_rules
        self.cost_profiles = cost_profiles
        self.eu = eu_countries or DEFAULT_EU

    # ------------------------------------------------------------------ lookups
    def route(self, source_country: str, resale_country: str) -> str:
        if source_country == resale_country:
            return "domestic"
        if source_country in self.eu and resale_country in self.eu:
            return "intra_eu"
        return "import"

    def fee_rule(self, side: str, marketplace: str | None, country: str | None, category: str | None) -> FeeRuleData | None:
        candidates = [
            r
            for r in self.fee_rules
            if r.side == side
            and (r.marketplace_code in (None, marketplace))
            and (r.country in (None, country))
            and (r.category_code in (None, category))
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r.specificity())

    def cost_profile(self, route: str, category: CategoryCosts) -> CostProfileData:
        best: tuple[int, CostProfileData] | None = None
        for p in self.cost_profiles:
            if p.route != route:
                continue
            if p.category_code and p.category_code != category.code:
                continue
            if p.shipping_class and p.shipping_class != category.shipping_class:
                continue
            spec = (4 if p.category_code else 0) + (2 if p.shipping_class else 0)
            if best is None or spec > best[0]:
                best = (spec, p)
        return best[1] if best else CostProfileData(route=route)

    # ------------------------------------------------------------------ costs
    def costs(self, purchase_price: float, sale_price: float, ctx: TradeContext) -> CostBreakdown:
        bd = CostBreakdown()
        route = self.route(ctx.source_country, ctx.resale_country)
        profile = self.cost_profile(route, ctx.category)

        # --- buy side
        buy_rule = self.fee_rule("buy", ctx.source_marketplace, ctx.source_country, ctx.category.code)
        if buy_rule and not ctx.local_pickup:
            fee, pay = buy_rule.compute(purchase_price)
            bd.add("Buyer protection fee", fee, "buy", ctx.source_marketplace)
            bd.add("Buyer payment fee", pay, "buy")
        if ctx.local_pickup:
            bd.add("Travel / pickup", profile.travel_eur, "buy")
        else:
            inbound = ctx.listing_shipping_eur if ctx.listing_shipping_eur is not None else profile.inbound_shipping_eur
            bd.add("Inbound shipping", inbound, "buy", "listing" if ctx.listing_shipping_eur is not None else route)
        bd.add("Transport insurance", purchase_price * profile.insurance_pct, "buy")
        if route == "import":
            dutiable = purchase_price + (ctx.listing_shipping_eur or profile.inbound_shipping_eur)
            duty = dutiable * profile.import_duty_pct
            bd.add("Import duty", duty, "buy", "estimate - check TARIC")
            bd.add("Import VAT", (dutiable + duty) * profile.import_vat_pct, "buy")
        bd.add("Misc. (buy)", profile.misc_eur, "buy")
        bd.add("Extra costs", ctx.extra_costs_eur, "buy")

        # --- preparation
        auth = ctx.category.authentication_required if ctx.include_authentication is None else ctx.include_authentication
        if auth:
            bd.add("Authentication", ctx.category.authentication_eur, "prep")
        refurb = (
            ctx.refurbishment_override_eur
            if ctx.refurbishment_override_eur is not None
            else ctx.category.refurbishment_eur
        )
        bd.add("Refurbishment / cleaning", refurb, "prep")

        # --- sell side
        sell_rule = self.fee_rule("sell", ctx.resale_marketplace, ctx.resale_country, ctx.category.code)
        if sell_rule:
            fee, pay = sell_rule.compute(sale_price)
            bd.add("Selling fee", fee, "sell", ctx.resale_marketplace)
            bd.add("Payment processing", pay, "sell")
        resale_profile = self.cost_profile("domestic", ctx.category)
        bd.add("Outbound shipping", resale_profile.outbound_shipping_eur, "sell")
        bd.add("Misc. (sell)", sale_price * profile.misc_pct, "sell")
        return bd

    def economics(self, purchase_price: float, sale_price: float, ctx: TradeContext) -> TradeEconomics:
        bd = self.costs(purchase_price, sale_price, ctx)
        capital = purchase_price + bd.total("buy") + bd.total("prep")
        net = sale_price - bd.total("sell") - capital
        roi = net / capital if capital > 0 else 0.0
        return TradeEconomics(purchase_price, sale_price, round(capital, 2), round(net, 2), round(roi, 4), bd)

    def max_buy_price(
        self,
        sale_price: float,
        ctx: TradeContext,
        *,
        target_roi: float,
        min_profit_eur: float = 0.0,
    ) -> float:
        """Largest purchase price for which ROI >= target_roi AND profit >= min_profit_eur.
        Solved by bisection so non-linear (tiered, min/max) fee rules are handled."""
        if sale_price <= 0:
            return 0.0

        def ok(p: float) -> bool:
            e = self.economics(p, sale_price, ctx)
            return e.roi >= target_roi and e.net_profit >= min_profit_eur

        lo, hi = 0.0, sale_price
        if not ok(lo):
            return 0.0
        for _ in range(50):
            mid = (lo + hi) / 2
            if ok(mid):
                lo = mid
            else:
                hi = mid
            if hi - lo < 0.5:
                break
        return round(lo, 0) if lo >= 10 else round(lo, 2)


def roi_from(net_profit: float, capital: float) -> float:
    return net_profit / capital if capital else 0.0


def max_buy_price_simple(quick_sale: float, costs: float, target_roi: float) -> float:
    """Closed form for fixed costs: (sale - costs) / (1 + roi). Matches the spec example:
    quick resale 1000, costs 100, ROI 25 % -> 720."""
    return max(0.0, (quick_sale - costs) / (1 + target_roi))
