"""Deterministic product normalisation pipeline.

Stages
------
1. text folding (accents, case) + language detection
2. accessory-only detection (box only, cases, chargers...) -> heavily penalised
3. candidate matching against the catalogue:
   reference numbers > title aliases/regex > description aliases/regex, gated by
   required keywords (e.g. "love" only counts together with "cartier") and
   excluded keywords (rings vs bracelets, controllers vs consoles...)
4. attribute extraction: generic (material, size, colour, condition, accessories)
   + product-specific attribute rules from the catalogue
5. confidence scoring 0..1 with human-readable reasons
6. optional AI fallback (see :mod:`arbscan.normalization.ai`) when the rule
   confidence is below a threshold - never required.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from arbscan.db.enums import Condition
from arbscan.normalization import dictionaries as D
from arbscan.normalization.text import compact, detect_language, fold


def _keyword_re(keyword: str) -> re.Pattern[str]:
    """Keywords are whole-word, accent-insensitive. Prefix with ``re:`` for a raw regex
    (evaluated against folded text), e.g. ``re:^(mando|controller)\\b``."""
    if keyword.startswith("re:"):
        return re.compile(keyword[3:], re.I)
    return re.compile(r"(?<![a-z0-9])" + re.escape(fold(keyword)) + r"(?![a-z0-9])")


@dataclass
class CatalogEntry:
    id: int | None
    slug: str
    name: str
    brand: str
    model: str
    category: str
    collection: str | None = None
    product_type: str | None = None
    aliases: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    reference_numbers: list[str] = field(default_factory=list)
    required_keywords: list[str] = field(default_factory=list)
    excluded_keywords: list[str] = field(default_factory=list)
    variant_attributes: dict[str, float] = field(default_factory=dict)
    attribute_rules: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    brand_aliases: list[str] = field(default_factory=list)

    def is_flag_attribute(self, attr: str) -> bool:
        """A flag attribute only ever takes one literal value (e.g. ``diamonds=yes``);
        its absence means the default variant, so it is never "missing"."""
        rules = (self.attribute_rules or {}).get(attr) or []
        values = {r.get("value") for r in rules}
        return bool(rules) and len(values) == 1 and all(v and "{" not in v for v in values)

    # compiled lazily
    _compiled: dict[str, Any] = field(default_factory=dict, repr=False)

    def compiled(self) -> dict[str, Any]:
        if not self._compiled:
            alias_res = [re.compile(r"(?<![a-z0-9])" + re.escape(fold(a)) + r"(?![a-z0-9])") for a in self.aliases if a]
            pattern_res = []
            for p in self.patterns:
                try:
                    pattern_res.append(re.compile(p, re.I))
                except re.error:
                    continue
            brand_terms = [fold(self.brand)] + [fold(b) for b in self.brand_aliases]
            self._compiled = {
                "aliases": alias_res,
                "patterns": pattern_res,
                "refs": [compact(r) for r in self.reference_numbers if len(compact(r)) >= 4],
                "required": [_keyword_re(k) for k in self.required_keywords if k],
                "excluded": [_keyword_re(k) for k in self.excluded_keywords if k],
                "brand": [re.compile(r"(?<![a-z0-9])" + re.escape(b) + r"(?![a-z0-9])") for b in brand_terms if b],
                "attr_rules": {
                    attr: [(re.compile(r["pattern"], re.I), r.get("value")) for r in rules]
                    for attr, rules in (self.attribute_rules or {}).items()
                },
            }
        return self._compiled


@dataclass
class NormalizationResult:
    product_slug: str | None = None
    product_id: int | None = None
    product_name: str | None = None
    brand: str | None = None
    model: str | None = None
    collection: str | None = None
    product_type: str | None = None
    category: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)
    variant_key: str = ""
    condition: str = Condition.UNKNOWN.value
    accessories: dict[str, bool] = field(default_factory=dict)
    authenticity_info: str | None = None
    language: str | None = None
    confidence: float = 0.0
    method: str = "rules"
    reasons: list[str] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    accessory_only: bool = False

    @property
    def matched(self) -> bool:
        return self.product_slug is not None

    def as_dict(self) -> dict[str, Any]:
        return {
            "product_slug": self.product_slug,
            "product_id": self.product_id,
            "brand": self.brand,
            "model": self.model,
            "collection": self.collection,
            "product_type": self.product_type,
            "category": self.category,
            "attributes": self.attributes,
            "variant_key": self.variant_key,
            "condition": self.condition,
            "accessories": self.accessories,
            "language": self.language,
            "confidence": round(self.confidence, 3),
            "method": self.method,
            "reasons": self.reasons,
            "candidates": self.candidates[:5],
            "accessory_only": self.accessory_only,
        }


CRITICAL_IMPORTANCE = 0.8


def make_variant_key(attributes: dict[str, str], variant_attrs: dict[str, float]) -> str:
    """Stable valuation key: only the *critical* attributes (importance >= 0.8) that were
    detected. Minor attributes (size, colour...) are handled by comparable weighting."""
    parts = [
        f"{k}={attributes[k]}"
        for k in sorted(variant_attrs)
        if attributes.get(k) and float(variant_attrs[k]) >= CRITICAL_IMPORTANCE
    ]
    return ";".join(parts)


def parse_variant_key(key: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (key or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k] = v
    return out


_COMPILED_GENERIC = {
    "materials": [(v, D.compile_all(p)) for v, p in D.MATERIALS],
    "colors": [(v, D.compile_all(p)) for v, p in D.COLORS],
    "conditions": [(v, D.compile_all(p)) for v, p in D.CONDITIONS],
    "size": D.compile_all(D.SIZE_PATTERNS),
    "case": re.compile(D.CASE_SIZE_PATTERN),
    "acc_neg": {k: D.compile_all(v) for k, v in D.ACCESSORY_NEGATIVE.items()},
    "acc_pos": {k: D.compile_all(v) for k, v in D.ACCESSORY_POSITIVE.items()},
    "acc_only": D.compile_all(D.ACCESSORY_ONLY_PATTERNS),
    "auth": D.compile_all(D.AUTHENTICITY_PATTERNS),
}


def detect_condition(text: str, raw_condition: str | None = None) -> str:
    """Map free text / marketplace condition labels to :class:`Condition`.
    A structured condition from the marketplace takes precedence over description text."""
    for source in (fold(raw_condition), text):
        if not source:
            continue
        for value, pats in _COMPILED_GENERIC["conditions"]:
            if any(p.search(source) for p in pats):
                return value.value
    return Condition.UNKNOWN.value


def detect_accessories(text: str) -> dict[str, bool]:
    found: dict[str, bool] = {}
    for key, negs in _COMPILED_GENERIC["acc_neg"].items():
        if any(p.search(text) for p in negs):
            found[key] = False
    for key, pos in _COMPILED_GENERIC["acc_pos"].items():
        if key in found:
            continue
        if any(p.search(text) for p in pos):
            found[key] = True
    return found


def detect_material(text: str) -> str | None:
    for value, pats in _COMPILED_GENERIC["materials"]:
        if any(p.search(text) for p in pats):
            return value
    return None


def detect_color(text: str) -> str | None:
    for value, pats in _COMPILED_GENERIC["colors"]:
        if any(p.search(text) for p in pats):
            return value
    return None


def detect_size(text: str) -> str | None:
    for p in _COMPILED_GENERIC["size"]:
        m = p.search(text)
        if m:
            return m.group(1)
    return None


def extract_authenticity_info(original_text: str) -> str | None:
    """Return the sentences that *mention* provenance/authenticity. This is reported
    verbatim as a seller claim and is never treated as proof of authenticity."""
    sentences = re.split(r"(?<=[.!?\n])\s+", original_text or "")
    hits = [s.strip() for s in sentences if any(p.search(fold(s)) for p in _COMPILED_GENERIC["auth"])]
    if not hits:
        return None
    return " ".join(hits)[:600]


def _attr_value(m: re.Match[str], value: str | None) -> str:
    """Resolve an attribute value from a rule match. ``value`` may be a literal, empty
    (-> first captured group, or whole match), or a template such as ``"m{0}_pro"``."""
    groups = [g for g in m.groups() if g is not None]
    if value and "{" in value:
        return value.format(*groups).strip()
    if value:
        return value
    return (groups[0] if groups else m.group(0)).strip().replace(" ", "")


class RuleNormalizer:
    """Deterministic normaliser built from catalogue entries."""

    def __init__(self, catalog: list[CatalogEntry]):
        self.catalog = catalog

    # ------------------------------------------------------------------ public
    def normalize(
        self,
        title: str,
        description: str = "",
        *,
        brand_hint: str | None = None,
        model_hint: str | None = None,
        condition_hint: str | None = None,
        category_hint: str | None = None,
    ) -> NormalizationResult:
        title_f = fold(" ".join(x for x in (title, brand_hint or "", model_hint or "") if x))
        desc_f = fold(description)
        full = f"{title_f} \n {desc_f}"
        result = NormalizationResult(language=detect_language(f"{title} {description}"))

        result.accessory_only = any(p.search(title_f) for p in _COMPILED_GENERIC["acc_only"])
        result.condition = detect_condition(full, condition_hint)
        result.accessories = detect_accessories(full)
        result.authenticity_info = extract_authenticity_info(f"{title}. {description}")

        scored = []
        for entry in self.catalog:
            score, why = self._score_entry(entry, title_f, desc_f)
            if score > 0:
                scored.append((score, entry, why))
        scored.sort(key=lambda x: x[0], reverse=True)
        result.candidates = [{"slug": e.slug, "score": round(s, 3)} for s, e, _ in scored[:5]]

        if not scored:
            result.reasons.append("no catalogue product matched")
            generic_brand = self._detect_any_brand(full)
            if generic_brand:
                result.brand = generic_brand
                result.confidence = 0.15
                result.reasons.append(f"brand '{generic_brand}' detected without a known model")
            return result

        best_score, entry, why = scored[0]
        result.reasons.extend(why)
        confidence = best_score

        # ambiguity: a different product scoring almost as high lowers confidence
        if len(scored) > 1 and scored[1][0] >= best_score - 0.05 and scored[1][1].slug != entry.slug:
            confidence -= 0.15
            result.reasons.append(f"ambiguous with '{scored[1][1].slug}'")

        attrs = self._extract_attributes(entry, title_f, full)
        result.attributes = attrs

        # critical variant attributes resolved -> more confidence; unresolved -> less
        for attr, importance in (entry.variant_attributes or {}).items():
            if float(importance) >= 0.8 and not entry.is_flag_attribute(attr):
                if attr in attrs:
                    confidence += 0.03
                else:
                    confidence -= 0.06
                    result.reasons.append(f"critical attribute '{attr}' not found")

        if result.accessory_only:
            confidence -= 0.55
            result.reasons.append("listing appears to sell an accessory/part only")

        if brand_hint and fold(brand_hint) and not any(p.search(fold(brand_hint)) for p in entry.compiled()["brand"]):
            confidence -= 0.2
            result.reasons.append(f"marketplace brand '{brand_hint}' conflicts with '{entry.brand}'")

        result.confidence = max(0.0, min(0.99, confidence))
        result.product_slug = entry.slug
        result.product_id = entry.id
        result.product_name = entry.name
        result.brand = entry.brand
        result.model = entry.model
        result.collection = entry.collection
        result.product_type = entry.product_type
        result.category = entry.category
        result.variant_key = make_variant_key(attrs, entry.variant_attributes or {})
        return result

    # ------------------------------------------------------------------ internals
    def _score_entry(self, entry: CatalogEntry, title_f: str, desc_f: str) -> tuple[float, list[str]]:
        c = entry.compiled()
        full = f"{title_f} {desc_f}"
        why: list[str] = []

        if c["excluded"] and any(p.search(title_f) for p in c["excluded"]):
            return 0.0, []
        brand_in_title = any(p.search(title_f) for p in c["brand"])
        brand_anywhere = brand_in_title or any(p.search(desc_f) for p in c["brand"])

        title_compact = compact(title_f)
        full_compact = compact(full)
        ref_hit = next((r for r in c["refs"] if r in title_compact), None) or next(
            (r for r in c["refs"] if r in full_compact), None
        )
        alias_title = any(p.search(title_f) for p in c["aliases"]) or any(p.search(title_f) for p in c["patterns"])
        alias_desc = any(p.search(desc_f) for p in c["aliases"]) or any(p.search(desc_f) for p in c["patterns"])
        strong_alias = any(p.search(title_f) for p in c["aliases"])

        # Required keywords gate weak pattern matches (e.g. "love" needs "cartier").
        # Explicit aliases ("love bracelet") and reference numbers are specific enough on their own.
        if c["required"] and not any(p.search(full) for p in c["required"]) and not (strong_alias or ref_hit):
            return 0.0, []

        score = 0.0
        if ref_hit:
            score = 0.93
            why.append(f"reference number {ref_hit.upper()} matched")
        elif alias_title:
            score = 0.72
            why.append("model alias/pattern matched in title")
        elif alias_desc:
            score = 0.45
            why.append("model alias/pattern matched in description only")
        else:
            return 0.0, []

        if brand_in_title:
            score += 0.15
            why.append(f"brand '{entry.brand}' in title")
        elif brand_anywhere:
            score += 0.07
            why.append(f"brand '{entry.brand}' in description")
        if c["excluded"] and any(p.search(desc_f) for p in c["excluded"]):
            score -= 0.12
            why.append("excluded keyword present in description")
        return score, why

    def _extract_attributes(self, entry: CatalogEntry, title_f: str, full: str) -> dict[str, str]:
        attrs: dict[str, str] = {}
        rules = entry.compiled()["attr_rules"]
        # product-specific rules first; title wins over description
        for attr, compiled_rules in rules.items():
            for source in (title_f, full):
                for pattern, value in compiled_rules:
                    m = pattern.search(source)
                    if m:
                        attrs[attr] = _attr_value(m, value)
                        break
                if attr in attrs:
                    break
        wanted = set(entry.variant_attributes or {}) | {"material", "size", "color"}
        if "material" in wanted and "material" not in attrs:
            mat = detect_material(title_f) or detect_material(full)
            if mat:
                attrs["material"] = mat
        if "size" in wanted and "size" not in attrs:
            size = detect_size(title_f) or detect_size(full)
            if size:
                attrs["size"] = size
        if "color" in (entry.variant_attributes or {}) and "color" not in attrs:
            color = detect_color(title_f) or detect_color(full)
            if color:
                attrs["color"] = color
        return attrs

    def _detect_any_brand(self, text: str) -> str | None:
        for entry in self.catalog:
            if any(p.search(text) for p in entry.compiled()["brand"]):
                return entry.brand
        return None
