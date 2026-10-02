"""Runtime-editable business settings stored in ``app_settings``."""

from __future__ import annotations

import copy
from typing import Any

from sqlalchemy.orm import Session

from arbscan.core.config import get_settings
from arbscan.db.models import AppSetting
from arbscan.scoring.engine import ScoringConfig
from arbscan.valuation.engine import ValuationConfig


def default_business() -> dict[str, Any]:
    s = get_settings()
    return {
        "resale_countries": [s.default_resale_country],
        "default_resale_marketplace": {"ES": "wallapop", "FR": "leboncoin", "DE": "ebay_de", "IT": "ebay_it"},
        "category_resale_marketplace": {},
        "target_roi": s.default_target_roi,
        "min_roi": s.default_min_roi,
        "min_profit_eur": 40.0,
        "local_pickup_cities": [],
        "comparable_lookback_days": 180,
        "show_unmatched_listings": False,
    }


def default_scanner() -> dict[str, Any]:
    return {
        "high_priority_minutes": 5,
        "standard_minutes": 30,
        "background_minutes": 180,
        "analysis_minutes": 360,
        "refresh_active_hours": 12,
        "expire_after_days_unseen": 7,
        "max_results_per_search": 50,
        "demo_feed_enabled": True,
    }


DEFAULTS = {
    "business": default_business,
    "scoring": lambda: ScoringConfig().as_dict(),
    "valuation": lambda: ValuationConfig().__dict__.copy(),
    "scanner": default_scanner,
}


def get_setting(session: Session, key: str) -> dict[str, Any]:
    base = copy.deepcopy(DEFAULTS[key]()) if key in DEFAULTS else {}
    row = session.get(AppSetting, key)
    if row and isinstance(row.value, dict):
        for k, v in row.value.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k] = {**base[k], **v}
            else:
                base[k] = v
    return base


def set_setting(session: Session, key: str, value: dict[str, Any]) -> dict[str, Any]:
    row = session.get(AppSetting, key)
    if row is None:
        row = AppSetting(key=key, value=value)
        session.add(row)
    else:
        merged = dict(row.value or {})
        merged.update(value)
        row.value = merged
    session.flush()
    return get_setting(session, key)


def scoring_config(session: Session) -> ScoringConfig:
    return ScoringConfig.from_dict(get_setting(session, "scoring"))


def valuation_config(session: Session) -> ValuationConfig:
    cfg = ValuationConfig()
    for k, v in get_setting(session, "valuation").items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg
