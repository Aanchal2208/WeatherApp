"""FastAPI router for data export in CSV, JSON, and PDF formats."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database import get_db
from backend.models import WeatherRecord
from backend.services.export import (
    export_records_to_csv,
    export_records_to_json,
    export_records_to_pdf,
)

router = APIRouter(prefix="/api/export", tags=["Data Export"])


def _fetch_records_for_export(
    db: Session,
    record_id: Optional[int] = None,
    q: Optional[str] = None,
):
    """Helper to query database records based on optional filters."""
    query = db.query(WeatherRecord)
    if record_id is not None:
        rec = query.filter(WeatherRecord.id == record_id).first()
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record {record_id} not found.",
            )
        return [rec.to_dict()]

    if q:
        like_expr = f"%{q.strip()}%"
        query = query.filter(
            or_(
                WeatherRecord.location_name.ilike(like_expr),
                WeatherRecord.location_query.ilike(like_expr),
                WeatherRecord.country.ilike(like_expr),
            )
        )

    records = query.order_by(WeatherRecord.id.desc()).all()
    return [r.to_dict() for r in records]


@router.get("/csv")
def download_csv(
    record_id: Optional[int] = Query(None, description="Export a specific record ID"),
    q: Optional[str] = Query(None, description="Filter records to export"),
    db: Session = Depends(get_db),
):
    """Exports weather records and observations to downloadable CSV."""
    records = _fetch_records_for_export(db, record_id=record_id, q=q)
    csv_data = export_records_to_csv(records)

    filename = f"weather_export_{record_id or 'all'}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/json")
def download_json(
    record_id: Optional[int] = Query(None, description="Export a specific record ID"),
    q: Optional[str] = Query(None, description="Filter records to export"),
    db: Session = Depends(get_db),
):
    """Exports weather records and observations to downloadable JSON."""
    records = _fetch_records_for_export(db, record_id=record_id, q=q)
    json_data = export_records_to_json(records)

    filename = f"weather_export_{record_id or 'all'}.json"
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/pdf")
def download_pdf(
    record_id: Optional[int] = Query(None, description="Export a specific record ID"),
    q: Optional[str] = Query(None, description="Filter records to export"),
    db: Session = Depends(get_db),
):
    """Exports weather records to a formatted executive PDF report."""
    records = _fetch_records_for_export(db, record_id=record_id, q=q)
    pdf_bytes = export_records_to_pdf(records)

    filename = f"weather_report_{record_id or 'all'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
