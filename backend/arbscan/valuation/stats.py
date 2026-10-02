"""Weighted robust statistics (no numpy dependency needed for these sizes)."""

from __future__ import annotations

import math
from collections.abc import Sequence


def weighted_quantile(values: Sequence[float], weights: Sequence[float], q: float) -> float:
    """Weighted quantile using the midpoint (Hazen-like) interpolation of cumulative weights."""
    if not values:
        raise ValueError("empty")
    pairs = sorted(zip(values, weights, strict=True))
    total = sum(w for _, w in pairs)
    if total <= 0:
        raise ValueError("weights sum to zero")
    cum = 0.0
    positions = []
    for v, w in pairs:
        positions.append(((cum + w / 2) / total, v))
        cum += w
    if q <= positions[0][0]:
        return positions[0][1]
    if q >= positions[-1][0]:
        return positions[-1][1]
    for (p0, v0), (p1, v1) in zip(positions, positions[1:], strict=False):
        if p0 <= q <= p1:
            if p1 == p0:
                return v1
            return v0 + (v1 - v0) * (q - p0) / (p1 - p0)
    return positions[-1][1]  # pragma: no cover


def weighted_median(values: Sequence[float], weights: Sequence[float]) -> float:
    return weighted_quantile(values, weights, 0.5)


def weighted_trimmed_mean(values: Sequence[float], weights: Sequence[float], trim: float = 0.1) -> float:
    lo = weighted_quantile(values, weights, trim)
    hi = weighted_quantile(values, weights, 1 - trim)
    kept = [(v, w) for v, w in zip(values, weights, strict=True) if lo <= v <= hi]
    if not kept:
        return weighted_median(values, weights)
    tw = sum(w for _, w in kept)
    return sum(v * w for v, w in kept) / tw


def robust_outlier_mask(values: Sequence[float], z_threshold: float = 3.0) -> list[bool]:
    """True = keep. Modified z-score on log prices (MAD based). With very few points,
    falls back to a ratio band around the median."""
    n = len(values)
    if n == 0:
        return []
    logs = [math.log(max(v, 1e-6)) for v in values]
    med = sorted(logs)[n // 2] if n % 2 else (sorted(logs)[n // 2 - 1] + sorted(logs)[n // 2]) / 2
    if n < 5:
        return [abs(lv - med) <= math.log(2.2) for lv in logs]
    deviations = sorted(abs(lv - med) for lv in logs)
    mad = deviations[n // 2] if n % 2 else (deviations[n // 2 - 1] + deviations[n // 2]) / 2
    if mad < 1e-9:
        return [abs(lv - med) <= math.log(1.6) for lv in logs]
    return [abs(0.6745 * (lv - med) / mad) <= z_threshold for lv in logs]
