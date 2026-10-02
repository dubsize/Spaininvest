"""Scan orchestration: which marketplace/watchlist is due, run it, record metrics.

Scheduling model
----------------
* ``tick()`` runs every ``SCANNER_TICK_SECONDS`` (Celery beat). It enqueues a scan for
  each enabled marketplace whose ``next_run_at`` has passed. ``poll_interval_seconds`` on
  the marketplace is a hard floor - we never hit a marketplace more often than that.
* Within a marketplace scan only the watchlists that are due are searched. A watchlist's
  interval comes from its own ``scan_interval_minutes`` or from its priority
  (high / standard / background, configurable in Settings > Scanner).
* Slower jobs: valuation snapshots + full re-scoring (``analysis_minutes``), expiry of
  listings not seen for N days, FX refresh.
"""

from __future__ import annotations

import time
import traceback
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from arbscan.alerts.service import AlertDispatcher
from arbscan.connectors.base import ConnectorDisabled, ConnectorNotConfigured, SearchQuery
from arbscan.connectors.registry import build_connector
from arbscan.core.logging import get_logger
from arbscan.db.enums import ConnectorStatus, ListingSource
from arbscan.db.models import Listing, Marketplace, ScanRun, Watchlist
from arbscan.normalization.catalog import normalizer_cache
from arbscan.services.fx import FxService
from arbscan.services.pipeline import Evaluator, ingest_raw_listing
from arbscan.services.settings_service import get_setting

log = get_logger(__name__)


def utcnow() -> datetime:
    return datetime.now(UTC)


def _aware(dt: datetime | None) -> datetime | None:
    return None if dt is None else (dt if dt.tzinfo else dt.replace(tzinfo=UTC))


def watchlist_interval_minutes(w: Watchlist, scanner_cfg: dict) -> int:
    if w.scan_interval_minutes:
        return int(w.scan_interval_minutes)
    return int(
        {
            "high": scanner_cfg["high_priority_minutes"],
            "standard": scanner_cfg["standard_minutes"],
            "background": scanner_cfg["background_minutes"],
        }.get(w.priority, scanner_cfg["standard_minutes"])
    )


def watchlist_query(w: Watchlist) -> SearchQuery:
    kw = (w.keyword or "").strip()
    if not kw and w.canonical_product is not None:
        kw = f"{w.canonical_product.brand} {w.canonical_product.model}"
    return SearchQuery(keywords=kw or w.name, max_price=w.max_price_eur, limit=50)


def watchlist_applies(w: Watchlist, mp: Marketplace) -> bool:
    if w.marketplaces and mp.code not in w.marketplaces:
        return False
    if w.countries and mp.country not in w.countries:
        return False
    return True


def due_marketplaces(session: Session, now: datetime | None = None) -> list[str]:
    now = now or utcnow()
    scanner_cfg = get_setting(session, "scanner")
    out = []
    for mp in session.scalars(select(Marketplace).where(Marketplace.enabled.is_(True))):
        if mp.connector_key == "demo" and not scanner_cfg.get("demo_feed_enabled", True):
            continue
        nxt = _aware(mp.next_run_at)
        if nxt is None or nxt <= now:
            out.append(mp.code)
    return out


def run_marketplace_scan(session: Session, marketplace_code: str, *, now: datetime | None = None, force: bool = False) -> ScanRun:
    now = now or utcnow()
    mp = session.get(Marketplace, marketplace_code)
    if mp is None:
        raise KeyError(marketplace_code)
    scanner_cfg = get_setting(session, "scanner")
    run = ScanRun(marketplace_code=mp.code, started_at=now, status="running")
    session.add(run)
    session.flush()
    t0 = time.monotonic()
    mp.last_run_at = now
    connector = build_connector(mp.connector_key, mp.code, {**(mp.config or {}), "requests_per_minute": mp.max_requests_per_minute})
    is_demo = mp.connector_key == "demo"

    try:
        if connector.is_stub:
            run.status = "skipped"
            run.error = connector.compliance.summary
            mp.status = ConnectorStatus.STUB.value
            return run
        if not connector.is_configured():
            raise ConnectorNotConfigured("credentials missing")

        # which searches are due?
        if is_demo:
            searches = [(None, SearchQuery(keywords="demo"))]
        else:
            searches = []
            for w in session.scalars(select(Watchlist).where(Watchlist.enabled.is_(True))):
                if not watchlist_applies(w, mp):
                    continue
                if not force and _aware(w.next_scan_at) and _aware(w.next_scan_at) > now:
                    continue
                q = watchlist_query(w)
                q.limit = int(scanner_cfg.get("max_results_per_search", 50))
                searches.append((w, q))

        fx = FxService(session)
        normalizer = normalizer_cache.get(session)
        changed_ids: list[int] = []
        price_drop_ids: set[int] = set()
        for w, q in searches:
            run.query = (run.query + " | " if run.query else "") + q.keywords[:80]
            raws = connector.search(q)
            run.listings_found += len(raws)
            for raw in raws:
                res = ingest_raw_listing(
                    session, raw,
                    source=ListingSource.DEMO.value if is_demo else ListingSource.CONNECTOR.value,
                    is_demo=is_demo, now=now, fx=fx, normalizer=normalizer,
                )
                if res.created:
                    run.listings_new += 1
                elif res.updated:
                    run.listings_updated += 1
                if res.price_changed:
                    run.price_changes += 1
                    if (res.price_change_pct or 0) < 0:
                        price_drop_ids.add(res.listing.id)
                if res.created or res.updated:
                    changed_ids.append(res.listing.id)
            if w is not None:
                w.last_scanned_at = now
                w.next_scan_at = now + timedelta(minutes=watchlist_interval_minutes(w, scanner_cfg))
        session.flush()

        # evaluate & alert
        if changed_ids:
            ev = Evaluator(session, now=now)
            dispatcher = AlertDispatcher(session, now=now)
            for listing in session.scalars(select(Listing).where(Listing.id.in_(changed_ids))):
                for opp in ev.evaluate(listing):
                    session.flush()
                    if opp.is_active:
                        run.opportunities_created += 1
                        run.alerts_sent += dispatcher.process(opp, price_dropped=listing.id in price_drop_ids)
        run.status = "success"
        mp.status = ConnectorStatus.OK.value
        mp.last_success_at = now
        mp.consecutive_failures = 0
        mp.total_listings_collected = (mp.total_listings_collected or 0) + run.listings_new
        return run
    except (ConnectorDisabled, ConnectorNotConfigured) as exc:
        run.status = "skipped"
        run.error = str(exc)
        mp.status = ConnectorStatus.NOT_CONFIGURED.value
        return run
    except Exception as exc:  # noqa: BLE001
        run.status = "error"
        run.error = f"{type(exc).__name__}: {exc}"[:2000]
        run.details = {"traceback": traceback.format_exc()[-4000:]}
        mp.status = ConnectorStatus.ERROR.value if mp.consecutive_failures >= 2 else ConnectorStatus.DEGRADED.value
        mp.last_error = run.error
        mp.last_error_at = now
        mp.consecutive_failures = (mp.consecutive_failures or 0) + 1
        log.error("scan failed", extra={"marketplace": mp.code, "err": run.error})
        return run
    finally:
        run.finished_at = utcnow()
        run.duration_ms = int((time.monotonic() - t0) * 1000)
        # back off exponentially on repeated failures, never faster than the poll floor
        backoff = 2 ** min(mp.consecutive_failures or 0, 5)
        mp.next_run_at = now + timedelta(seconds=mp.poll_interval_seconds * backoff)
        session.flush()
        log.info(
            "scan finished",
            extra={
                "marketplace": mp.code, "status": run.status, "duration_ms": run.duration_ms,
                "found": run.listings_found, "new": run.listings_new, "updated": run.listings_updated,
                "price_changes": run.price_changes, "opportunities": run.opportunities_created,
            },
        )
        connector.close()


def expire_unseen_listings(session: Session, now: datetime | None = None) -> int:
    now = now or utcnow()
    days = int(get_setting(session, "scanner").get("expire_after_days_unseen", 7))
    cutoff = now - timedelta(days=days)
    n = 0
    for listing in session.scalars(
        select(Listing).where(
            Listing.status == "active",
            Listing.source == ListingSource.CONNECTOR.value,
            Listing.last_seen_at < cutoff,
        )
    ):
        listing.status = "ended"
        listing.ended_at = listing.last_seen_at
        n += 1
    return n
