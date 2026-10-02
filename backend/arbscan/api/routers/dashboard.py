"""Main screen: 'Where can I deploy €1 today for the highest risk-adjusted return?'"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from arbscan.api.deps import DB, User
from arbscan.api.schemas import OpportunityOut
from arbscan.db.models import AlertEvent, Listing, Marketplace, Opportunity, ScanRun
from arbscan.services.deals import portfolio_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _ser(rows: list[Opportunity]) -> list[dict]:
    return [OpportunityOut.model_validate(o).model_dump(mode="json") for o in rows]


@router.get("")
def dashboard(db: Session = DB, user: str = User, limit: int = 8) -> dict:
    now = datetime.now(UTC)
    base = (
        select(Opportunity)
        .join(Listing, Listing.id == Opportunity.listing_id)
        .where(Opportunity.is_active.is_(True), Opportunity.opportunity_type != "NONE")
    )
    profitable = base.where(Opportunity.opportunity_type.in_(["FLIP", "CROSS_BORDER"]))
    not_high_risk = profitable.where(Opportunity.risk_level != "HIGH")

    def top(stmt, *order):  # noqa: ANN001
        return _ser(db.scalars(stmt.order_by(*order).limit(limit)).unique().all())

    # risk-adjusted capital efficiency: annualised ROI x confidence x (1 - risk) - the
    # "best place for the next euro" ranking (does not blindly use discount %)
    deploy_candidates = db.scalars(not_high_risk.where(Opportunity.net_profit_quick_eur > 0)).unique().all()

    def deploy_key(o: Opportunity) -> float:
        conf = o.confidence_score or 0
        return (o.annualized_roi or 0) * (0.4 + 0.6 * conf) * (1 - (o.risk_score or 0) / 100) * (0.5 + o.score / 200)

    deploy = sorted(deploy_candidates, key=deploy_key, reverse=True)[:limit]

    active_count = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    agg = db.execute(
        select(
            func.count(), func.sum(Opportunity.net_profit_quick_eur), func.sum(Opportunity.purchase_price_eur),
            func.avg(Opportunity.roi),
        ).select_from(Opportunity).where(
            Opportunity.is_active.is_(True), Opportunity.opportunity_type.in_(["FLIP", "CROSS_BORDER"]),
            Opportunity.risk_level != "HIGH",
        )
    ).one()
    new_24h = db.scalar(
        select(func.count()).select_from(base.where(Listing.first_seen_at >= now - timedelta(hours=24)).subquery())
    ) or 0
    alerts_24h = db.scalar(select(func.count(AlertEvent.id)).where(AlertEvent.created_at >= now - timedelta(hours=24))) or 0
    connectors = db.scalars(select(Marketplace).where(Marketplace.enabled.is_(True))).all()
    last_scan = db.scalar(select(func.max(ScanRun.finished_at)).where(ScanRun.status == "success"))

    return {
        "generated_at": now.isoformat(),
        "kpis": {
            "active_opportunities": active_count,
            "actionable_deals": agg[0] or 0,
            "expected_profit_eur": round(agg[1] or 0, 2),
            "capital_required_eur": round(agg[2] or 0, 2),
            "average_roi": round(agg[3] or 0, 4) if agg[3] is not None else None,
            "new_last_24h": new_24h,
            "alerts_last_24h": alerts_24h,
            "listings_tracked": db.scalar(select(func.count(Listing.id)).where(Listing.status == "active")) or 0,
            "last_successful_scan": last_scan.isoformat() if last_scan else None,
        },
        "deploy_now": _ser(deploy),
        "hottest": top(base, Opportunity.score.desc()),
        "newest": top(base, func.coalesce(Listing.published_at, Listing.first_seen_at).desc()),
        "highest_profit": top(not_high_risk, Opportunity.net_profit_quick_eur.desc().nulls_last()),
        "highest_roi": top(not_high_risk, Opportunity.roi.desc().nulls_last()),
        "highest_liquidity": top(not_high_risk, Opportunity.liquidity_score.desc().nulls_last(), Opportunity.score.desc()),
        "cross_border": top(base.where(Opportunity.opportunity_type == "CROSS_BORDER"), Opportunity.score.desc()),
        "negotiation": top(base.where(Opportunity.opportunity_type == "NEGOTIATION"), Opportunity.profit_at_target_offer_eur.desc().nulls_last()),
        "price_reduced": top(base.where(Listing.price_drop_count > 0), Listing.last_price_change_at.desc().nulls_last()),
        "connectors": [
            {"code": m.code, "name": m.name, "status": m.status, "last_success_at": m.last_success_at, "next_run_at": m.next_run_at}
            for m in connectors
        ],
        "portfolio": portfolio_summary(db, now),
    }
