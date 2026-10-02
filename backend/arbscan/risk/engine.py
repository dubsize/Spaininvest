"""Rules-based risk engine.

Produces LOW / MEDIUM / HIGH with an explanation. It never classifies a listing as
fraud: it surfaces *signals* for a human to check. Each rule is a small function so
new rules can be added (and unit-tested) independently.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from arbscan.db.enums import RiskLevel
from arbscan.normalization import dictionaries as D
from arbscan.normalization.text import fold

AUTH_WARNING = "Authentication required before purchase. The scanner does not certify authenticity."


@dataclass
class RiskInput:
    title: str
    description: str = ""
    price_eur: float = 0.0
    market_value_eur: float | None = None
    quick_sale_eur: float | None = None
    valuation_confidence: str | None = None
    country: str | None = None
    city: str | None = None
    marketplace_country: str | None = None
    seller_rating: float | None = None
    seller_rating_count: int | None = None
    seller_account_created_at: datetime | None = None
    seller_type: str | None = None
    image_urls: list[str] = field(default_factory=list)
    is_luxury: bool = False
    accessories: dict[str, bool] = field(default_factory=dict)
    authenticity_info: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)
    known_references: list[str] = field(default_factory=list)
    normalization_confidence: float = 1.0
    normalization_reasons: list[str] = field(default_factory=list)
    accessory_only: bool = False
    # cross-listing signals computed by the service layer from the DB
    duplicate_image_listings: int = 0
    duplicate_text_listings: int = 0
    duplicate_text_cities: int = 0
    seller_high_value_listings: int = 0
    seller_distinct_categories: int = 0
    shipping_available: bool | None = None
    now: datetime | None = None


@dataclass
class RiskFlag:
    code: str
    severity: str  # info | low | medium | high
    points: float
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "severity": self.severity, "points": self.points, "message": self.message}


@dataclass
class RiskResult:
    level: str
    score: float
    flags: list[RiskFlag]
    requires_authentication: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def reasons(self) -> list[str]:
        return [f.message for f in self.flags if f.points > 0]

    @property
    def positives(self) -> list[str]:
        return [f.message for f in self.flags if f.points <= 0]


Rule = Callable[[RiskInput, str], list[RiskFlag]]
_COUNTERFEIT = D.compile_all(D.COUNTERFEIT_PATTERNS)
_OFF_PLATFORM = D.compile_all(D.OFF_PLATFORM_PATTERNS)
_UNPROTECTED = D.compile_all(D.UNPROTECTED_PAYMENT_PATTERNS)
_STOCK = D.compile_all(D.STOCK_PHOTO_PATTERNS)
_URGENCY = [re.compile(p) for p in (
    r"urgente?", r"\burgent\b", r"\bdringend\b", r"necesito (el )?dinero", r"besoin d'argent", r"brauche geld",
    r"\bregalo\b(?! de)", r"precio (de )?chollo", r"solo hoy", r"aujourd'hui seulement", r"nur heute",
    r"primero que (llegue|venga)", r"premier arrive", r"wer zuerst kommt",
)]


def rule_price_vs_market(i: RiskInput, text: str) -> list[RiskFlag]:
    if not i.market_value_eur or i.price_eur <= 0:
        return []
    ratio = i.price_eur / i.market_value_eur
    if ratio < 0.35:
        return [RiskFlag("PRICE_ABSURD", "high", 40, f"price is {ratio:.0%} of market value - far too good to be true")]
    if ratio < 0.55:
        return [RiskFlag("PRICE_VERY_LOW", "medium", 22, f"price is {ratio:.0%} of market value - materially below market")]
    if ratio < 0.72:
        return [RiskFlag("PRICE_LOW", "low", 8, f"price materially below market ({ratio:.0%} of value)")]
    return []


def rule_seller_account(i: RiskInput, text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    now = i.now or datetime.now(UTC)
    if i.seller_account_created_at:
        age_days = (now - i.seller_account_created_at).days
        if age_days < 14:
            flags.append(RiskFlag("SELLER_NEW", "medium", 18, f"seller account is only {age_days} days old"))
        elif age_days < 60:
            flags.append(RiskFlag("SELLER_RECENT", "low", 8, f"seller account is {age_days} days old"))
    if i.seller_rating_count is not None:
        if i.seller_rating_count == 0:
            flags.append(RiskFlag("SELLER_NO_RATINGS", "medium", 14, "seller has no ratings"))
        elif i.seller_rating_count < 5:
            flags.append(RiskFlag("SELLER_FEW_RATINGS", "low", 7, f"seller has only {i.seller_rating_count} review(s)"))
        elif i.seller_rating_count >= 30 and (i.seller_rating or 0) >= 4.5:
            flags.append(RiskFlag("SELLER_ESTABLISHED", "info", -6, f"established seller ({i.seller_rating_count} reviews, {i.seller_rating:.1f}/5)"))
    if i.seller_rating is not None and i.seller_rating_count and i.seller_rating_count >= 3 and i.seller_rating < 3.5:
        flags.append(RiskFlag("SELLER_LOW_RATING", "medium", 15, f"seller rating is low ({i.seller_rating:.1f}/5)"))
    return flags


def rule_off_platform(i: RiskInput, text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    hits = sorted({p.pattern for p in _OFF_PLATFORM if p.search(text)})
    if hits:
        flags.append(RiskFlag("OFF_PLATFORM_PAYMENT", "high", 30, "asks to communicate/pay outside the marketplace or uses unusual payment terms"))
    elif any(p.search(text) for p in _UNPROTECTED):
        flags.append(RiskFlag("UNPROTECTED_PAYMENT", "low", 8, "mentions payment methods without buyer protection (bank transfer/Bizum)"))
    if D.EMAIL_PATTERN.search(i.description or "") or len(D.PHONE_PATTERN.findall(i.description or "")) > 0:
        flags.append(RiskFlag("CONTACT_IN_TEXT", "medium", 12, "contact details (phone/e-mail) embedded in the listing text"))
    return flags


def rule_counterfeit_language(i: RiskInput, text: str) -> list[RiskFlag]:
    hits = [p.pattern for p in _COUNTERFEIT if p.search(text)]
    if not hits:
        return []
    sev, pts = ("high", 45) if i.is_luxury else ("medium", 15)
    return [RiskFlag("COUNTERFEIT_WORDING", sev, pts, "wording suggests a replica/'inspired' item (e.g. 'replica', 'AAA', 'style', 'tipo')")]


def rule_photos(i: RiskInput, text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    if any(p.search(text) for p in _STOCK):
        flags.append(RiskFlag("STOCK_PHOTO_TEXT", "medium", 15, "description says photos are illustrative / from the internet"))
    hosts = [u for u in i.image_urls if any(h in u.lower() for h in D.STOCK_IMAGE_HOSTS)]
    if hosts:
        flags.append(RiskFlag("STOCK_IMAGE_HOST", "medium", 15, "images are hosted on brand/stock-photo domains (not original photos)"))
    if not i.image_urls:
        flags.append(RiskFlag("NO_PHOTOS", "medium", 12, "no photos"))
    elif len(i.image_urls) == 1 and i.is_luxury:
        flags.append(RiskFlag("SINGLE_PHOTO", "low", 7, "only one photo for a luxury item"))
    elif len(i.image_urls) >= 4 and not hosts:
        flags.append(RiskFlag("ORIGINAL_PHOTOS", "info", -4, f"{len(i.image_urls)} photos, original photos appear present"))
    if i.duplicate_image_listings > 0:
        flags.append(RiskFlag("DUPLICATE_IMAGES", "high", 25, f"same image(s) used in {i.duplicate_image_listings} other listing(s)"))
    return flags


def rule_duplicates(i: RiskInput, text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    if i.duplicate_text_cities >= 2:
        flags.append(RiskFlag("DUPLICATE_CITIES", "high", 25, f"identical listing posted in {i.duplicate_text_cities + 1} cities"))
    elif i.duplicate_text_listings >= 1:
        flags.append(RiskFlag("CROSS_POSTED", "low", 5, f"same item also listed {i.duplicate_text_listings} other time(s) (cross-posting is common)"))
    return flags


def rule_seller_inventory(i: RiskInput, text: str) -> list[RiskFlag]:
    if i.seller_type == "professional":
        return []
    if i.seller_high_value_listings >= 5 and i.seller_distinct_categories >= 3:
        return [RiskFlag("SELLER_MANY_HIGH_VALUE", "medium", 18, f"private seller offers {i.seller_high_value_listings} unrelated high-value items")]
    return []


def rule_luxury_provenance(i: RiskInput, text: str) -> list[RiskFlag]:
    if not i.is_luxury:
        return []
    flags: list[RiskFlag] = []
    has_docs = i.accessories.get("papers") or i.accessories.get("receipt")
    if not has_docs:
        flags.append(RiskFlag("NO_PROVENANCE", "low", 10, "luxury item without papers/receipt mentioned"))
    else:
        flags.append(RiskFlag("PROVENANCE_CLAIMED", "info", -3, "seller mentions papers/receipt (unverified claim)"))
    if i.accessories.get("papers") is False and i.accessories.get("box") is False:
        flags.append(RiskFlag("NO_BOX_NO_PAPERS", "low", 5, "explicitly sold without box and papers"))
    return flags


def rule_reference_consistency(i: RiskInput, text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    ref = i.attributes.get("reference")
    known = {re.sub(r"[^a-z0-9]", "", r.lower()) for r in i.known_references}
    if ref and known and re.sub(r"[^a-z0-9]", "", ref.lower()) not in known:
        flags.append(RiskFlag("UNKNOWN_REFERENCE", "medium", 12, f"reference '{ref}' is not a known reference for this model"))
    # conflicting details: several different materials/sizes mentioned in the title
    mats = {v for v, pats in D.MATERIALS[:5] if any(re.search(p, fold(i.title)) for p in pats)}
    if len(mats) >= 2 and "two_tone" not in mats:
        flags.append(RiskFlag("CONFLICTING_MATERIALS", "low", 8, f"title mentions conflicting materials ({', '.join(sorted(mats))})"))
    if any("conflicts with" in r for r in i.normalization_reasons):
        flags.append(RiskFlag("CONFLICTING_BRAND", "medium", 12, "marketplace brand field conflicts with the title"))
    return flags


def rule_location(i: RiskInput, text: str) -> list[RiskFlag]:
    if i.marketplace_country and i.country and i.country != i.marketplace_country:
        return [RiskFlag("LOCATION_MISMATCH", "low", 8, f"item located in {i.country} on a {i.marketplace_country} marketplace")]
    if re.search(r"(estoy|vivo) (en|fuera)|je suis (a|en) l'etranger|bin im ausland|currently abroad|i am abroad", text):
        return [RiskFlag("SELLER_ABROAD", "medium", 15, "seller says they are abroad / item must be shipped")]
    return []


def rule_urgency(i: RiskInput, text: str) -> list[RiskFlag]:
    if any(p.search(text) for p in _URGENCY):
        return [RiskFlag("URGENCY", "low", 6, "pressure/urgency language")]
    return []


def rule_listing_quality(i: RiskInput, text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    if len((i.description or "").strip()) < 15 and i.price_eur >= 500:
        flags.append(RiskFlag("THIN_DESCRIPTION", "low", 6, "very short description for a high-value item"))
    if i.accessory_only:
        flags.append(RiskFlag("ACCESSORY_ONLY", "medium", 12, "listing may be for an accessory/box only, not the product"))
    if i.normalization_confidence < 0.5:
        flags.append(RiskFlag("UNCERTAIN_MATCH", "low", 6, "product identification is uncertain"))
    if i.shipping_available is False and i.is_luxury and i.marketplace_country and i.country and i.country != i.marketplace_country:
        flags.append(RiskFlag("NO_SHIPPING_ABROAD", "low", 4, "pickup only, item abroad"))
    return flags


DEFAULT_RULES: list[Rule] = [
    rule_price_vs_market,
    rule_seller_account,
    rule_off_platform,
    rule_counterfeit_language,
    rule_photos,
    rule_duplicates,
    rule_seller_inventory,
    rule_luxury_provenance,
    rule_reference_consistency,
    rule_location,
    rule_urgency,
    rule_listing_quality,
]


class RiskEngine:
    def __init__(self, rules: list[Rule] | None = None, medium_threshold: float = 22, high_threshold: float = 45):
        self.rules = rules or DEFAULT_RULES
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold

    def evaluate(self, i: RiskInput) -> RiskResult:
        text = fold(f"{i.title}\n{i.description}")
        flags: list[RiskFlag] = []
        for rule in self.rules:
            flags.extend(rule(i, text))
        score = max(0.0, sum(f.points for f in flags))
        has_high = any(f.severity == "high" for f in flags)
        if score >= self.high_threshold or (has_high and score >= self.medium_threshold + 10):
            level = RiskLevel.HIGH
        elif score >= self.medium_threshold or has_high:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        warnings = [AUTH_WARNING] if i.is_luxury else []
        flags.sort(key=lambda f: -f.points)
        return RiskResult(level.value, round(min(score, 100), 1), flags, requires_authentication=i.is_luxury, warnings=warnings)
