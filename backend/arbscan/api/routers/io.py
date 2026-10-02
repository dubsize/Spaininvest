"""CSV import / export."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from arbscan.api.deps import DB, User
from arbscan.services import csv_io

router = APIRouter(prefix="/io", tags=["import-export"])
MAX_UPLOAD = 5 * 1024 * 1024


def _csv(text: str, name: str) -> Response:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M")
    return Response(
        content=text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}-{stamp}.csv"'},
    )


@router.get("/export/opportunities.csv")
def export_opportunities(db: Session = DB, user: str = User, include_inactive: bool = False) -> Response:
    return _csv(csv_io.export_opportunities(db, include_inactive), "deals")


@router.get("/export/price-history.csv")
def export_history(db: Session = DB, user: str = User, product_id: int | None = None) -> Response:
    return _csv(csv_io.export_price_history(db, product_id), "price-history")


@router.get("/export/watchlists.csv")
def export_watchlists(db: Session = DB, user: str = User) -> Response:
    return _csv(csv_io.export_watchlists(db), "watchlists")


async def _read_upload(file: UploadFile) -> str:
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "file too large (max 5 MB)")
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise HTTPException(400, "could not decode file")


@router.post("/import/watchlists")
async def import_watchlists(file: UploadFile = File(...), db: Session = DB, user: str = User) -> dict:
    return csv_io.import_watchlists(db, await _read_upload(file))


@router.post("/import/listings")
async def import_listings(file: UploadFile = File(...), db: Session = DB, user: str = User) -> dict:
    return csv_io.import_listings(db, await _read_upload(file))


@router.get("/templates/{kind}.csv")
def template(kind: str, user: str = User) -> Response:
    if kind == "listings":
        cols = csv_io.LISTING_IMPORT_COLUMNS
        example = "https://es.wallapop.com/item/thermomix-tm6-123456789,Thermomix TM6 como nuevo,650,EUR,wallapop,ES,Madrid,Con varoma,like_new,Lucia,4.8,23,2026-01-15,0,,asking,,,active"
    elif kind == "watchlists":
        cols = csv_io.WATCHLIST_COLUMNS
        example = "Thermomix TM6,Thermomix TM6,thermomix-tm6,kitchen_appliances,Vorwerk,ES | DE,,700,20,80,20,70,high,5,yes"
    else:
        raise HTTPException(404, "unknown template")
    return _csv("﻿" + ",".join(cols) + "\n" + example + "\n", f"{kind}-template")
