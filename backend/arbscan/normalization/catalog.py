"""Building normaliser catalogues from YAML seed data or the database."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from arbscan.normalization.engine import CatalogEntry, RuleNormalizer

SEED_CATALOG = Path(__file__).resolve().parent.parent / "seed" / "data" / "catalog.yaml"


def load_seed_yaml(path: Path = SEED_CATALOG) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def entry_from_dict(d: dict[str, Any], id_: int | None = None) -> CatalogEntry:
    return CatalogEntry(
        id=id_,
        slug=d["slug"],
        name=d.get("name") or d["slug"],
        brand=d["brand"],
        model=d.get("model") or d.get("name") or d["slug"],
        category=d.get("category") or d.get("category_code") or "other",
        collection=d.get("collection"),
        product_type=d.get("product_type"),
        aliases=list(d.get("aliases") or []),
        patterns=list(d.get("patterns") or []),
        reference_numbers=[str(r) for r in d.get("reference_numbers") or []],
        required_keywords=list(d.get("required_keywords") or []),
        excluded_keywords=list(d.get("excluded_keywords") or []),
        variant_attributes=dict(d.get("variant_attributes") or {}),
        attribute_rules=dict(d.get("attribute_rules") or {}),
        brand_aliases=list(d.get("brand_aliases") or []),
    )


def entries_from_seed() -> list[CatalogEntry]:
    data = load_seed_yaml()
    return [entry_from_dict(p, i + 1) for i, p in enumerate(data["products"])]


def entry_from_model(p: Any) -> CatalogEntry:
    aliases = list(p.aliases or [])
    patterns = list(p.patterns or [])
    if not aliases and not patterns and not p.reference_numbers:
        # user-created product without explicit rules: fall back to the model name
        aliases = [p.model]
    return CatalogEntry(
        id=p.id,
        slug=p.slug,
        name=p.name,
        brand=p.brand,
        model=p.model,
        category=p.category_code,
        collection=p.collection,
        product_type=p.product_type,
        aliases=aliases,
        patterns=patterns,
        reference_numbers=[str(r) for r in p.reference_numbers or []],
        required_keywords=list(p.required_keywords or []),
        excluded_keywords=list(p.excluded_keywords or []),
        variant_attributes=dict(p.variant_attributes or {}),
        attribute_rules=dict(p.attribute_rules or {}),
        brand_aliases=list(p.brand_aliases or []),
    )


class NormalizerCache:
    """Process-wide cache of the rule normaliser, rebuilt when products change
    (``invalidate``) or after ``ttl`` seconds."""

    def __init__(self, ttl: float = 300):
        self.ttl = ttl
        self._lock = threading.Lock()
        self._normalizer: RuleNormalizer | None = None
        self._built_at = 0.0

    def get(self, session: Session) -> RuleNormalizer:
        from arbscan.db.models import CanonicalProduct

        with self._lock:
            if self._normalizer is None or time.monotonic() - self._built_at > self.ttl:
                products = session.scalars(select(CanonicalProduct).where(CanonicalProduct.is_active.is_(True))).all()
                self._normalizer = RuleNormalizer([entry_from_model(p) for p in products])
                self._built_at = time.monotonic()
            return self._normalizer

    def invalidate(self) -> None:
        with self._lock:
            self._normalizer = None


normalizer_cache = NormalizerCache()
