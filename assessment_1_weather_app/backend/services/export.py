"""Data export service generating downloadable CSV, JSON, and PDF files.

Includes PM Accelerator organizational metadata and developer credit: Aanchal Singh.
"""

import csv
import io
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from backend.services.integrations import PM_ACCELERATOR_DETAILS


def export_records_to_csv(records: List[Dict[str, Any]]) -> str:
    """Flattens weather records into CSV string with daily detail rows."""
    output = io.StringIO()
    fieldnames = [
        "record_id",
        "location_query",
        "location_name",
        "country",
        "latitude",
        "longitude",
        "date_start",
        "date_end",
        "observation_date",
        "temp_max_c",
        "temp_min_c",
        "temp_mean_c",
        "precipitation_mm",
        "wind_speed_max_kmh",
        "weather_code",
        "weather_description",
        "created_at",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for rec in records:
        daily_records = rec.get("daily_records", [])
        if not daily_records:
            # Output parent record with blank daily fields
            writer.writerow({
                "record_id": rec.get("id"),
                "location_query": rec.get("location_query"),
                "location_name": rec.get("location_name"),
                "country": rec.get("country"),
                "latitude": rec.get("latitude"),
                "longitude": rec.get("longitude"),
                "date_start": rec.get("date_start"),
                "date_end": rec.get("date_end"),
                "observation_date": "",
                "temp_max_c": "",
                "temp_min_c": "",
                "temp_mean_c": "",
                "precipitation_mm": "",
                "wind_speed_max_kmh": "",
                "weather_code": "",
                "weather_description": "",
                "created_at": rec.get("created_at"),
            })
        else:
            for d in daily_records:
                writer.writerow({
                    "record_id": rec.get("id"),
                    "location_query": rec.get("location_query"),
                    "location_name": rec.get("location_name"),
                    "country": rec.get("country"),
                    "latitude": rec.get("latitude"),
                    "longitude": rec.get("longitude"),
                    "date_start": rec.get("date_start"),
                    "date_end": rec.get("date_end"),
                    "observation_date": d.get("date"),
                    "temp_max_c": d.get("temp_max"),
                    "temp_min_c": d.get("temp_min"),
                    "temp_mean_c": d.get("temp_mean"),
                    "precipitation_mm": d.get("precipitation_sum"),
                    "wind_speed_max_kmh": d.get("wind_speed_max"),
                    "weather_code": d.get("weather_code"),
                    "weather_description": d.get("weather_description"),
                    "created_at": rec.get("created_at"),
                })

    return output.getvalue()


def export_records_to_json(records: List[Dict[str, Any]]) -> str:
    """Serializes weather records into a well-structured JSON string with metadata."""
    payload = {
        "metadata": {
            "project": "Weather Intelligence Platform",
            "developer": PM_ACCELERATOR_DETAILS["developer"],
            "organization": PM_ACCELERATOR_DETAILS["organization"],
            "website": PM_ACCELERATOR_DETAILS["website"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(records),
        },
        "records": records,
    }
    return json.dumps(payload, indent=2)


def export_records_to_pdf(records: List[Dict[str, Any]]) -> bytes:
    """Generates an executive PDF report with styling and tables using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("Weather Intelligence Platform — Technical Assessment", title_style))
    elements.append(
        Paragraph(
            f"Developer: <b>{PM_ACCELERATOR_DETAILS['developer']}</b> | "
            f"Organization: <b>{PM_ACCELERATOR_DETAILS['organization']}</b> | "
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3182CE"), spaceAfter=12))

    # Executive Overview
    elements.append(Paragraph("PM Accelerator Mission & Project Overview", section_heading))
    elements.append(
        Paragraph(
            f"{PM_ACCELERATOR_DETAILS['mission']}<br/><br/>"
            f"This report presents weather search persistence, external API telemetry, "
            f"and historical daily climate records stored in PostgreSQL. Total Saved Records: <b>{len(records)}</b>.",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 10))

    # Summary Table of Records
    elements.append(Paragraph("Saved Weather Records Summary", section_heading))
    summary_data = [
        ["ID", "Location", "Coordinates", "Date Range", "Days", "Created At"]
    ]

    for rec in records[:15]:  # Summarize top 15 records in the main table
        daily_count = len(rec.get("daily_records", []))
        summary_data.append([
            str(rec.get("id")),
            Paragraph(f"<b>{rec.get('location_name')}</b> ({rec.get('country') or 'N/A'})", table_cell),
            f"{rec.get('latitude', 0):.2f}, {rec.get('longitude', 0):.2f}",
            f"{rec.get('date_start')} to {rec.get('date_end')}",
            str(daily_count),
            rec.get("created_at", "")[:10] if rec.get("created_at") else "",
        ])

    sum_table = Table(summary_data, colWidths=[30, 160, 90, 140, 40, 80])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
    ]))
    elements.append(sum_table)

    # Detailed Daily Weather Breakdown for Primary Record
    if records:
        primary = records[0]
        daily_items = primary.get("daily_records", [])
        if daily_items:
            elements.append(Spacer(1, 14))
            elements.append(
                Paragraph(
                    f"Daily Breakdown: {primary.get('location_name')} ({primary.get('date_start')} to {primary.get('date_end')})",
                    section_heading,
                )
            )

            detail_data = [
                ["Date", "Max Temp", "Min Temp", "Mean Temp", "Precipitation", "Wind Max", "Condition"]
            ]

            for d in daily_items[:12]:
                detail_data.append([
                    d.get("date", ""),
                    f"{d.get('temp_max')} °C" if d.get("temp_max") is not None else "--",
                    f"{d.get('temp_min')} °C" if d.get("temp_min") is not None else "--",
                    f"{d.get('temp_mean')} °C" if d.get("temp_mean") is not None else "--",
                    f"{d.get('precipitation_sum')} mm" if d.get("precipitation_sum") is not None else "0 mm",
                    f"{d.get('wind_speed_max')} km/h" if d.get("wind_speed_max") is not None else "--",
                    Paragraph(d.get("weather_description") or "N/A", table_cell),
                ])

            det_table = Table(detail_data, colWidths=[70, 70, 70, 70, 80, 80, 100])
            det_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A5568")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ]))
            elements.append(det_table)

    doc.build(elements)
    return buffer.getvalue()
