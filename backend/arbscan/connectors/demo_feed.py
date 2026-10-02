"""Demo feed: simulates a live connector by emitting a few fresh synthetic listings per
scan, so the full pipeline (scan -> normalise -> value -> score -> alert) can be watched
without any marketplace credentials. Listings are flagged ``is_demo``."""

from __future__ import annotations

import random
from typing import Any

from arbscan.connectors.base import ComplianceInfo, Connector, HealthStatus, RawListing, SearchQuery
from arbscan.seed.demo import generate_live_listing


class DemoFeedConnector(Connector):
    key = "demo"
    display_name = "Demo feed (synthetic)"
    countries = ["ES", "FR", "DE"]
    default_poll_seconds = 300
    compliance = ComplianceInfo(method="synthetic", summary="Synthetic data generator for demos and tests. No network access.")

    def __init__(self, marketplace_code: str, config: dict[str, Any] | None = None, seed: int | None = None):
        super().__init__(marketplace_code, config)
        self.rnd = random.Random(seed)

    def search(self, query: SearchQuery) -> list[RawListing]:
        # one call per scan run (the scanner calls it once with a generic query)
        n = self.rnd.choices([0, 1, 2, 3], weights=[2, 4, 3, 1])[0]
        out = []
        for _ in range(n):
            d = generate_live_listing(self.rnd)
            d.raw.source_metadata["demo_feed"] = True
            out.append(d.raw)
        return out

    def get_listing(self, external_id: str) -> RawListing | None:
        return None

    def normalize_listing(self, payload: dict[str, Any]) -> RawListing:
        return RawListing(**payload)

    def health_check(self) -> HealthStatus:
        return HealthStatus("OK", "synthetic data")
