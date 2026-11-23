"""Data export service — JSON, CSV, XML, PDF, Markdown.

Generates downloadable files from weather records stored in the database.
"""

import csv
import io
import json
from datetime import date
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# PM Accelerator description (required by assessment)
PM_ACCELERATOR_INFO = (
    "Product Manager Accelerator -- The Product Manager Accelerator Program "
    "is designed to support PM professionals through every stage of their "
    "career. From students looking for entry-level jobs to Directors looking "
    "to take on a VP role, our program has helped over hundreds of students "
    "land top PM roles at companies like Google, Facebook, Amazon, Uber, "
    "PayPal, and more. Our game plan consists of three core components: "
    "PM Curriculum, Weekly Mentorship, and Personalized Career Coaching. "
    "LinkedIn: https://www.linkedin.com/company/product-manager-accelerator/"
)

AUTHOR_NAME = "Aanchal"


def _prepare_flat_rows(records: list[dict]) -> list[dict]:
    """Flatten weather records into tabular rows for CSV/table export.

    Each daily entry in a record becomes its own row.
    """
    rows = []
    for rec in records:
        weather = rec.get("weather_data", {})

        # If weather_data contains daily arrays, expand each day
        time_arr = weather.get("time", [])
        if time_arr:
            for i, dt in enumerate(time_arr):
                row = {
                    "record_id": rec["id"],
                    "location_query": rec["location_query"],
                    "location_name": rec["location_name"],
                    "latitude": rec["latitude"],
                    "longitude": rec["longitude"],
                    "country": rec.get("country", ""),
                    "date": dt,
                    "temp_max": _safe_index(weather.get("temperature_2m_max"), i),
                    "temp_min": _safe_index(weather.get("temperature_2m_min"), i),
                    "feels_like_max": _safe_index(weather.get("apparent_temperature_max"), i),
                    "feels_like_min": _safe_index(weather.get("apparent_temperature_min"), i),
                    "precipitation_mm": _safe_index(weather.get("precipitation_sum"), i),
                    "rain_mm": _safe_index(weather.get("rain_sum"), i),
                    "snowfall_cm": _safe_index(weather.get("snowfall_sum"), i),
                    "wind_speed_max_kmh": _safe_index(weather.get("wind_speed_10m_max"), i),
                    "weather_code": _safe_index(weather.get("weather_code"), i),
                    "weather_description": _safe_index(weather.get("weather_description"), i),
                    "sunrise": _safe_index(weather.get("sunrise"), i),
                    "sunset": _safe_index(weather.get("sunset"), i),
                    "created_at": rec.get("created_at", ""),
                }
                rows.append(row)
        else:
            # Fallback: single summary row
            rows.append({
                "record_id": rec["id"],
                "location_query": rec["location_query"],
                "location_name": rec["location_name"],
                "latitude": rec["latitude"],
                "longitude": rec["longitude"],
                "country": rec.get("country", ""),
                "date_start": rec.get("date_start", ""),
                "date_end": rec.get("date_end", ""),
                "weather_summary": json.dumps(weather)[:500],
                "created_at": rec.get("created_at", ""),
            })
    return rows


def _safe_index(arr, i):
    """Safely index into an array that may be None or short."""
    if arr is None:
        return None
    try:
        return arr[i]
    except (IndexError, TypeError):
        return None


# ===== JSON Export =====

def export_json(records: list[dict]) -> str:
    """Export records as a formatted JSON string."""
    export_data = {
        "app": "Weather App",
        "author": AUTHOR_NAME,
        "about": PM_ACCELERATOR_INFO,
        "exported_at": date.today().isoformat(),
        "total_records": len(records),
        "records": records,
    }
    return json.dumps(export_data, indent=2, default=str)


# ===== CSV Export =====

def export_csv(records: list[dict]) -> str:
    """Export records as CSV (comma-delimited)."""
    rows = _prepare_flat_rows(records)
    if not rows:
        return f"# Weather App - Author: {AUTHOR_NAME}\n# {PM_ACCELERATOR_INFO}\n# No records to export.\n"

    output = io.StringIO()
    # Header comments
    output.write(f"# Weather App - Author: {AUTHOR_NAME}\n")
    output.write(f"# {PM_ACCELERATOR_INFO}\n")
    output.write(f"# Exported: {date.today().isoformat()}\n")

    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    return output.getvalue()


# ===== XML Export =====

def export_xml(records: list[dict]) -> str:
    """Export records as XML."""
    root = Element("WeatherExport")

    meta = SubElement(root, "Metadata")
    SubElement(meta, "App").text = "Weather App"
    SubElement(meta, "Author").text = AUTHOR_NAME
    SubElement(meta, "About").text = PM_ACCELERATOR_INFO
    SubElement(meta, "ExportedAt").text = date.today().isoformat()
    SubElement(meta, "TotalRecords").text = str(len(records))

    records_el = SubElement(root, "Records")
    for rec in records:
        record_el = SubElement(records_el, "Record", id=str(rec["id"]))
        SubElement(record_el, "LocationQuery").text = str(rec.get("location_query", ""))
        SubElement(record_el, "LocationName").text = str(rec.get("location_name", ""))
        SubElement(record_el, "Latitude").text = str(rec.get("latitude", ""))
        SubElement(record_el, "Longitude").text = str(rec.get("longitude", ""))
        SubElement(record_el, "Country").text = str(rec.get("country", ""))
        SubElement(record_el, "DateStart").text = str(rec.get("date_start", ""))
        SubElement(record_el, "DateEnd").text = str(rec.get("date_end", ""))
        SubElement(record_el, "CreatedAt").text = str(rec.get("created_at", ""))

        weather = rec.get("weather_data", {})
        weather_el = SubElement(record_el, "WeatherData")

        time_arr = weather.get("time", [])
        for i, dt in enumerate(time_arr):
            day_el = SubElement(weather_el, "Day", date=str(dt))
            SubElement(day_el, "TempMax").text = str(_safe_index(weather.get("temperature_2m_max"), i) or "")
            SubElement(day_el, "TempMin").text = str(_safe_index(weather.get("temperature_2m_min"), i) or "")
            SubElement(day_el, "Precipitation").text = str(_safe_index(weather.get("precipitation_sum"), i) or "")
            SubElement(day_el, "WindSpeedMax").text = str(_safe_index(weather.get("wind_speed_10m_max"), i) or "")
            SubElement(day_el, "WeatherDescription").text = str(_safe_index(weather.get("weather_description"), i) or "")

    # Pretty print
    rough = tostring(root, encoding="unicode")
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent="  ")


# ===== Markdown Export =====

def export_markdown(records: list[dict]) -> str:
    """Export records as a Markdown document."""
    lines = [
        f"# Weather App — Data Export",
        f"",
        f"**Author:** {AUTHOR_NAME}  ",
        f"**Exported:** {date.today().isoformat()}  ",
        f"**Total Records:** {len(records)}",
        f"",
        f"---",
        f"",
        f"## About — PM Accelerator",
        f"",
        f"{PM_ACCELERATOR_INFO}",
        f"",
        f"---",
        f"",
    ]

    for rec in records:
        lines.append(f"## Record #{rec['id']}: {rec['location_name']}")
        lines.append(f"")
        lines.append(f"- **Query:** {rec['location_query']}")
        lines.append(f"- **Coordinates:** {rec['latitude']}, {rec['longitude']}")
        lines.append(f"- **Country:** {rec.get('country', 'N/A')}")
        lines.append(f"- **Date Range:** {rec['date_start']} → {rec['date_end']}")
        lines.append(f"- **Created:** {rec.get('created_at', 'N/A')}")
        lines.append(f"")

        weather = rec.get("weather_data", {})
        time_arr = weather.get("time", [])
        if time_arr:
            lines.append(f"| Date | Max °C | Min °C | Precip (mm) | Wind (km/h) | Conditions |")
            lines.append(f"|------|--------|--------|-------------|-------------|------------|")
            for i, dt in enumerate(time_arr):
                t_max = _safe_index(weather.get("temperature_2m_max"), i) or "—"
                t_min = _safe_index(weather.get("temperature_2m_min"), i) or "—"
                precip = _safe_index(weather.get("precipitation_sum"), i) or "0"
                wind = _safe_index(weather.get("wind_speed_10m_max"), i) or "—"
                desc = _safe_index(weather.get("weather_description"), i) or "—"
                icon = _safe_index(weather.get("weather_icon"), i) or ""
                lines.append(f"| {dt} | {t_max} | {t_min} | {precip} | {wind} | {icon} {desc} |")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"")

    return "\n".join(lines)


# ===== PDF Export =====

def export_pdf(records: list[dict]) -> bytes:
    """Export records as a PDF document.

    Returns raw PDF bytes.
    """
    from fpdf import FPDF

    class WeatherPDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 14)
            self.cell(0, 10, "Weather App - Data Export", new_x="LMARGIN", new_y="NEXT", align="C")
            self.set_font("Helvetica", "", 9)
            self.cell(0, 5, f"Author: {AUTHOR_NAME}  |  Exported: {date.today().isoformat()}", new_x="LMARGIN", new_y="NEXT", align="C")
            self.ln(3)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 7)
            self.cell(0, 10, f"Page {self.page_no()}/{{nb}}  |  PM Accelerator", align="C")

    pdf = WeatherPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # About page
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "About - Product Manager Accelerator", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, PM_ACCELERATOR_INFO)
    pdf.ln(5)

    if not records:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 10, "No records to export.", new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())

    for rec in records:
        pdf.add_page()

        # Record header
        pdf.set_font("Helvetica", "B", 12)
        # Sanitize text for PDF (remove emojis/non-latin1 chars)
        location = _sanitize_for_pdf(rec["location_name"])
        pdf.cell(0, 8, f"Record #{rec['id']}: {location}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, f"Query: {_sanitize_for_pdf(rec['location_query'])}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, f"Coordinates: {rec['latitude']}, {rec['longitude']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, f"Country: {_sanitize_for_pdf(rec.get('country', 'N/A'))}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, f"Date Range: {rec['date_start']} to {rec['date_end']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, f"Created: {rec.get('created_at', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Weather data table
        weather = rec.get("weather_data", {})
        time_arr = weather.get("time", [])
        if time_arr:
            pdf.set_font("Helvetica", "B", 8)
            col_widths = [22, 18, 18, 22, 20, 45, 45]
            headers = ["Date", "Max C", "Min C", "Precip mm", "Wind km/h", "Sunrise", "Conditions"]
            for w, h in zip(col_widths, headers):
                pdf.cell(w, 6, h, border=1, align="C")
            pdf.ln()

            pdf.set_font("Helvetica", "", 7)
            for i, dt in enumerate(time_arr):
                t_max = str(_safe_index(weather.get("temperature_2m_max"), i) or "-")
                t_min = str(_safe_index(weather.get("temperature_2m_min"), i) or "-")
                precip = str(_safe_index(weather.get("precipitation_sum"), i) or "0")
                wind = str(_safe_index(weather.get("wind_speed_10m_max"), i) or "-")
                sunrise = str(_safe_index(weather.get("sunrise"), i) or "-")
                desc = _sanitize_for_pdf(str(_safe_index(weather.get("weather_description"), i) or "-"))

                vals = [str(dt), t_max, t_min, precip, wind, sunrise[-5:] if len(sunrise) > 5 else sunrise, desc]
                for w, v in zip(col_widths, vals):
                    pdf.cell(w, 5, v, border=1, align="C")
                pdf.ln()

    return bytes(pdf.output())


def _sanitize_for_pdf(text: str) -> str:
    """Remove/replace characters that fpdf2's latin-1 encoder can't handle."""
    if not text:
        return ""
    # Replace common Unicode characters with ASCII equivalents
    replacements = {
        "\u2014": "--",   # em-dash
        "\u2013": "-",    # en-dash
        "\u2018": "'",    # left single quote
        "\u2019": "'",    # right single quote
        "\u201c": '"',    # left double quote
        "\u201d": '"',    # right double quote
        "\u2026": "...",  # ellipsis
        "\u00b0": " deg", # degree sign (sometimes issues)
        "\u2192": "->",   # right arrow
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")
