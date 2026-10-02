"""Optional AI normalisation layer.

The application works without it (``AI_NORMALIZER=none``, the default). When enabled
(``AI_NORMALIZER=anthropic`` + ``ANTHROPIC_API_KEY``, ``pip install 'arbscan[ai]'``) it is
consulted **only** when the deterministic rules are unsure (confidence below
``AI_MIN_RULE_CONFIDENCE``), and it is constrained:

* it may only choose a product that already exists in the catalogue (or none);
* its confidence is capped at ``AI_CONFIDENCE_CAP`` so it never outranks an exact rule/SKU match;
* attributes are re-extracted by the rule engine for the chosen product; the model's
  attributes only fill gaps for that product's declared variant attributes;
* any error/refusal falls back silently to the rule result.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Protocol

from arbscan.core.config import get_settings
from arbscan.core.logging import get_logger
from arbscan.normalization.engine import CatalogEntry, NormalizationResult, RuleNormalizer, make_variant_key
from arbscan.normalization.text import fold

log = get_logger(__name__)

AI_CONFIDENCE_CAP = 0.8
MAX_CANDIDATES = 40

SYSTEM_PROMPT = (
    "You map second-hand marketplace listings (Spanish, French, German, Italian, Portuguese or English) "
    "to a fixed product catalogue. Choose the single catalogue product the listing is actually selling, "
    "or null when it sells something else (an accessory, a box, a part, a different model, a replica). "
    "Never invent products that are not in the list. Report attributes only when the listing states them. "
    "Confidence is your probability (0-1) that the chosen product is correct."
)


class AINormalizer(Protocol):
    def maybe_improve(self, listing: Any, result: NormalizationResult, normalizer: RuleNormalizer) -> NormalizationResult: ...


class NullAINormalizer:
    def maybe_improve(self, listing: Any, result: NormalizationResult, normalizer: RuleNormalizer) -> NormalizationResult:
        return result


def _candidates(listing: Any, result: NormalizationResult, normalizer: RuleNormalizer) -> list[CatalogEntry]:
    by_slug = {e.slug: e for e in normalizer.catalog}
    picked: list[CatalogEntry] = [by_slug[c["slug"]] for c in result.candidates if c["slug"] in by_slug]
    text = fold(f"{listing.title} {listing.description or ''}")
    for e in normalizer.catalog:
        if e not in picked and any(p.search(text) for p in e.compiled()["brand"]):
            picked.append(e)
    if len(picked) < 5:
        picked += [e for e in normalizer.catalog if e not in picked]
    return picked[:MAX_CANDIDATES]


def _schema(slugs: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "product_slug": {"anyOf": [{"type": "string", "enum": slugs}, {"type": "null"}]},
            "attributes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "value": {"type": "string"}},
                    "required": ["name", "value"],
                    "additionalProperties": False,
                },
            },
            "confidence": {"type": "number"},
            "reason": {"type": "string"},
        },
        "required": ["product_slug", "attributes", "confidence", "reason"],
        "additionalProperties": False,
    }


class AnthropicNormalizer:
    """Claude-backed fallback. ``client`` is injectable for tests."""

    def __init__(self, client: Any | None = None, model: str | None = None, min_rule_confidence: float | None = None):
        s = get_settings()
        if client is None:
            import anthropic  # optional dependency: pip install 'arbscan[ai]'

            client = anthropic.Anthropic(api_key=s.anthropic_api_key or None)
        self.client = client
        self.model = model or s.anthropic_model
        self.min_rule_confidence = s.ai_min_rule_confidence if min_rule_confidence is None else min_rule_confidence

    def maybe_improve(self, listing: Any, result: NormalizationResult, normalizer: RuleNormalizer) -> NormalizationResult:
        if result.confidence >= self.min_rule_confidence:
            return result
        candidates = _candidates(listing, result, normalizer)
        catalogue = "\n".join(
            f"- {e.slug}: {e.name} (brand {e.brand}; variant attributes: {', '.join(e.variant_attributes) or 'none'})"
            for e in candidates
        )
        user = (
            f"Catalogue:\n{catalogue}\n\n"
            f"Listing title: {listing.title}\n"
            f"Marketplace brand field: {listing.brand_raw or '-'}\n"
            f"Listing description:\n{listing.description or '-'}"
        )
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=2000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=SYSTEM_PROMPT,
                output_config={"effort": "low", "format": {"type": "json_schema", "schema": _schema([e.slug for e in candidates])}},
                messages=[{"role": "user", "content": user}],
            )
            if response.stop_reason == "refusal":
                log.info("ai normaliser refused", extra={"listing": getattr(listing, "id", None)})
                return result
            text = next(b.text for b in response.content if b.type == "text")
            data = json.loads(text)
        except Exception as exc:  # noqa: BLE001 - AI is best-effort, rules remain authoritative
            log.warning("ai normaliser failed", extra={"err": str(exc)[:300]})
            return result
        return self._merge(result, data, normalizer, listing)

    def _merge(self, result: NormalizationResult, data: dict[str, Any], normalizer: RuleNormalizer, listing: Any) -> NormalizationResult:
        slug = data.get("product_slug")
        entry = next((e for e in normalizer.catalog if e.slug == slug), None)
        if entry is None:
            return replace(result, reasons=[*result.reasons, f"AI: no catalogue product ({data.get('reason', '')[:120]})"])
        conf = max(0.0, min(AI_CONFIDENCE_CAP, float(data.get("confidence") or 0)))
        if conf <= result.confidence and slug != result.product_slug:
            return result
        title_f = fold(listing.title)
        attrs = normalizer._extract_attributes(entry, title_f, fold(f"{listing.title} {listing.description or ''}"))
        for a in data.get("attributes") or []:
            name, value = str(a.get("name", "")), str(a.get("value", "")).strip().lower().replace(" ", "_")
            if name in (entry.variant_attributes or {}) and name not in attrs and value:
                attrs[name] = value
        return replace(
            result,
            product_slug=entry.slug, product_id=entry.id, product_name=entry.name, brand=entry.brand, model=entry.model,
            collection=entry.collection, product_type=entry.product_type, category=entry.category,
            attributes=attrs, variant_key=make_variant_key(attrs, entry.variant_attributes or {}),
            confidence=max(result.confidence, conf) if slug == result.product_slug else conf,
            method="rules+ai", reasons=[*result.reasons, f"AI: {data.get('reason', '')[:200]}"],
        )


def get_ai_normalizer() -> AINormalizer | None:
    s = get_settings()
    if s.ai_normalizer == "anthropic":
        try:
            return AnthropicNormalizer()
        except Exception as exc:  # noqa: BLE001 - missing SDK/key must not break scanning
            log.warning("AI normaliser unavailable", extra={"err": str(exc)})
    return None
