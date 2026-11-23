"""Weather App — Flask Application.

A full-featured weather application with CRUD persistence, multiple API
integrations, and data export capabilities.

Author: Aanchal
Assessment: Tech Assessment 2 — Weather App (Backend Engineers)
"""

import json
from datetime import date, datetime, timedelta

from flask import Flask, jsonify, render_template, request, Response
from config import Config
from models import db, WeatherRecord
from services.geocoding import geocode
from services.weather import get_current_weather, get_historical_weather, get_air_quality
from services.integrations import (
    search_youtube_videos,
    get_wikipedia_summary,
    get_country_info,
    get_sunrise_sunset,
)
from services.export import export_json, export_csv, export_xml, export_pdf, export_markdown


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


# ===========================================================================
# Error handlers
# ===========================================================================

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": str(e.description)}), 400


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found."}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error. Please try again later."}), 500


# ===========================================================================
# Frontend route
# ===========================================================================

@app.route("/")
def index():
    """Serve the single-page frontend."""
    return render_template("index.html")


# ===========================================================================
# GEOCODING — Location validation
# ===========================================================================

@app.route("/api/geocode", methods=["GET"])
def api_geocode():
    """Resolve a location query to coordinates.

    Query params:
        q (str): Location string (city, zip, coordinates, landmark, etc.)

    Returns:
        JSON with resolved location details.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    try:
        location = geocode(query)
        return jsonify({"success": True, "location": location})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503


# ===========================================================================
# CURRENT WEATHER
# ===========================================================================

@app.route("/api/weather/current", methods=["GET"])
def api_current_weather():
    """Get current weather for a location.

    Query params:
        q (str): Location query string.

    Returns:
        JSON with current weather + location details.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    try:
        location = geocode(query)
        weather = get_current_weather(location["latitude"], location["longitude"])
        air_quality = get_air_quality(location["latitude"], location["longitude"])
        sun_data = get_sunrise_sunset(location["latitude"], location["longitude"])

        return jsonify({
            "success": True,
            "location": location,
            "weather": weather,
            "air_quality": air_quality,
            "sun": sun_data,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


# ===========================================================================
# CRUD OPERATIONS
# ===========================================================================

# ----- CREATE -----

@app.route("/api/weather", methods=["POST"])
def create_weather_record():
    """CREATE: Fetch weather for a location + date range, store in database.

    Request JSON body:
        location (str): Location query string.
        date_start (str): Start date in YYYY-MM-DD format.
        date_end (str): End date in YYYY-MM-DD format.

    Returns:
        JSON with the created record.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    location_query = (data.get("location") or "").strip()
    date_start_str = (data.get("date_start") or "").strip()
    date_end_str = (data.get("date_end") or "").strip()

    # --- Validate required fields ---
    errors = []
    if not location_query:
        errors.append("'location' is required.")
    if not date_start_str:
        errors.append("'date_start' is required (YYYY-MM-DD).")
    if not date_end_str:
        errors.append("'date_end' is required (YYYY-MM-DD).")
    if errors:
        return jsonify({"error": "Validation failed.", "details": errors}), 400

    # --- Validate date formats ---
    try:
        start = date.fromisoformat(date_start_str)
    except ValueError:
        return jsonify({"error": f"Invalid date_start format: '{date_start_str}'. Use YYYY-MM-DD."}), 400

    try:
        end = date.fromisoformat(date_end_str)
    except ValueError:
        return jsonify({"error": f"Invalid date_end format: '{date_end_str}'. Use YYYY-MM-DD."}), 400

    # --- Validate date range ---
    if end < start:
        return jsonify({"error": "date_end must be on or after date_start."}), 400

    if (end - start).days > 365:
        return jsonify({"error": "Date range cannot exceed 365 days."}), 400

    min_date = date(1940, 1, 1)
    max_date = date.today() + timedelta(days=16)
    if start < min_date:
        return jsonify({"error": f"date_start cannot be before {min_date.isoformat()}."}), 400
    if end > max_date:
        return jsonify({"error": f"date_end cannot be after {max_date.isoformat()} (16-day forecast limit)."}), 400

    # --- Validate location (geocode) ---
    try:
        location = geocode(location_query)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503

    # --- Fetch weather data ---
    try:
        weather_data = get_historical_weather(
            location["latitude"], location["longitude"], start, end
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 503

    # --- Store in database ---
    record = WeatherRecord(
        location_query=location_query,
        location_name=location["name"],
        latitude=location["latitude"],
        longitude=location["longitude"],
        country=location.get("country", ""),
        timezone=location.get("timezone", ""),
        date_start=start,
        date_end=end,
        weather_data=json.dumps(weather_data, default=str),
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Weather record created successfully.",
        "record": record.to_dict(),
    }), 201


# ----- READ -----

@app.route("/api/weather", methods=["GET"])
def read_weather_records():
    """READ: Get all weather records from the database.

    Query params (optional):
        location (str): Filter by location name (partial match).
        page (int): Page number (default 1).
        per_page (int): Records per page (default 50, max 200).

    Returns:
        JSON with list of records.
    """
    location_filter = request.args.get("location", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)

    query = WeatherRecord.query.order_by(WeatherRecord.created_at.desc())

    if location_filter:
        query = query.filter(
            WeatherRecord.location_name.ilike(f"%{location_filter}%")
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "records": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    })


@app.route("/api/weather/<int:record_id>", methods=["GET"])
def read_weather_record(record_id):
    """READ: Get a single weather record by ID.

    Returns:
        JSON with the record details.
    """
    record = db.session.get(WeatherRecord, record_id)
    if not record:
        return jsonify({"error": f"Record with ID {record_id} not found."}), 404

    return jsonify({"success": True, "record": record.to_dict()})


# ----- UPDATE -----

@app.route("/api/weather/<int:record_id>", methods=["PUT"])
def update_weather_record(record_id):
    """UPDATE: Update a weather record.

    Updatable fields:
    - location: Re-geocode and re-fetch weather for a new location
    - date_start / date_end: Re-fetch weather for a new date range
    - Both location and dates can be updated simultaneously

    Non-updatable: id, created_at (immutable metadata)

    Request JSON body:
        location (str, optional): New location query.
        date_start (str, optional): New start date.
        date_end (str, optional): New end date.

    Returns:
        JSON with the updated record.
    """
    record = db.session.get(WeatherRecord, record_id)
    if not record:
        return jsonify({"error": f"Record with ID {record_id} not found."}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    # Determine what's being updated
    new_location = (data.get("location") or "").strip()
    new_start_str = (data.get("date_start") or "").strip()
    new_end_str = (data.get("date_end") or "").strip()

    if not new_location and not new_start_str and not new_end_str:
        return jsonify({
            "error": "At least one field must be provided: 'location', 'date_start', or 'date_end'."
        }), 400

    # Resolve values (use existing if not provided)
    location = None
    if new_location:
        try:
            location = geocode(new_location)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except ConnectionError as e:
            return jsonify({"error": str(e)}), 503

    start = record.date_start
    end = record.date_end

    if new_start_str:
        try:
            start = date.fromisoformat(new_start_str)
        except ValueError:
            return jsonify({"error": f"Invalid date_start: '{new_start_str}'. Use YYYY-MM-DD."}), 400

    if new_end_str:
        try:
            end = date.fromisoformat(new_end_str)
        except ValueError:
            return jsonify({"error": f"Invalid date_end: '{new_end_str}'. Use YYYY-MM-DD."}), 400

    # Validate date range
    if end < start:
        return jsonify({"error": "date_end must be on or after date_start."}), 400
    if (end - start).days > 365:
        return jsonify({"error": "Date range cannot exceed 365 days."}), 400

    min_date = date(1940, 1, 1)
    max_date = date.today() + timedelta(days=16)
    if start < min_date:
        return jsonify({"error": f"date_start cannot be before {min_date.isoformat()}."}), 400
    if end > max_date:
        return jsonify({"error": f"date_end cannot be after {max_date.isoformat()}."}), 400

    # Re-fetch weather if location or dates changed
    lat = location["latitude"] if location else record.latitude
    lon = location["longitude"] if location else record.longitude

    needs_refetch = (
        new_location or new_start_str or new_end_str
    )

    if needs_refetch:
        try:
            weather_data = get_historical_weather(lat, lon, start, end)
        except (ValueError, ConnectionError) as e:
            return jsonify({"error": str(e)}), 400

        record.weather_data = json.dumps(weather_data, default=str)

    # Apply updates
    if location:
        record.location_query = new_location
        record.location_name = location["name"]
        record.latitude = location["latitude"]
        record.longitude = location["longitude"]
        record.country = location.get("country", "")

    record.date_start = start
    record.date_end = end

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Record updated successfully.",
        "record": record.to_dict(),
    })


# ----- DELETE -----

@app.route("/api/weather/<int:record_id>", methods=["DELETE"])
def delete_weather_record(record_id):
    """DELETE: Remove a weather record from the database.

    Returns:
        JSON confirmation.
    """
    record = db.session.get(WeatherRecord, record_id)
    if not record:
        return jsonify({"error": f"Record with ID {record_id} not found."}), 404

    location_name = record.location_name
    db.session.delete(record)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Record #{record_id} ({location_name}) deleted successfully.",
    })


# ===========================================================================
# API INTEGRATIONS
# ===========================================================================

@app.route("/api/integrations/youtube", methods=["GET"])
def api_youtube():
    """Get YouTube videos about a location."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    result = search_youtube_videos(query)
    return jsonify({"success": True, **result})


@app.route("/api/integrations/wikipedia", methods=["GET"])
def api_wikipedia():
    """Get Wikipedia summary for a location."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    result = get_wikipedia_summary(query)
    return jsonify({"success": True, **result})


@app.route("/api/integrations/country", methods=["GET"])
def api_country():
    """Get country information."""
    code = request.args.get("code", "").strip()
    if not code:
        return jsonify({"error": "Query parameter 'code' is required (ISO alpha-2)."}), 400

    result = get_country_info(code)
    if not result:
        return jsonify({"error": f"Country not found for code '{code}'."}), 404

    return jsonify({"success": True, "country": result})


@app.route("/api/integrations/explore", methods=["GET"])
def api_explore():
    """Combined exploration endpoint: Wikipedia + YouTube + Country info.

    Returns all integration data for a location in one call.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    country_code = request.args.get("country_code", "").strip()

    result = {
        "success": True,
        "wikipedia": get_wikipedia_summary(query),
        "youtube": search_youtube_videos(query),
    }

    if country_code:
        result["country"] = get_country_info(country_code)

    return jsonify(result)


# ===========================================================================
# DATA EXPORT
# ===========================================================================

@app.route("/api/export/<format_type>", methods=["GET"])
def api_export(format_type):
    """Export all weather records in the specified format.

    Path params:
        format_type: One of 'json', 'csv', 'xml', 'pdf', 'markdown'

    Query params (optional):
        ids: Comma-separated record IDs to export (default: all)

    Returns:
        Downloadable file in the requested format.
    """
    format_type = format_type.lower()
    valid_formats = {"json", "csv", "xml", "pdf", "markdown", "md"}
    if format_type not in valid_formats:
        return jsonify({
            "error": f"Invalid format '{format_type}'. Valid: {', '.join(sorted(valid_formats))}"
        }), 400

    # Optionally filter by IDs
    ids_param = request.args.get("ids", "").strip()
    if ids_param:
        try:
            ids = [int(x.strip()) for x in ids_param.split(",") if x.strip()]
            records = WeatherRecord.query.filter(WeatherRecord.id.in_(ids)).all()
        except ValueError:
            return jsonify({"error": "Invalid 'ids' parameter. Use comma-separated integers."}), 400
    else:
        records = WeatherRecord.query.order_by(WeatherRecord.created_at.desc()).all()

    record_dicts = [r.to_dict() for r in records]

    if format_type == "json":
        content = export_json(record_dicts)
        return Response(
            content,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=weather_export.json"},
        )

    elif format_type == "csv":
        content = export_csv(record_dicts)
        return Response(
            content,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=weather_export.csv"},
        )

    elif format_type == "xml":
        content = export_xml(record_dicts)
        return Response(
            content,
            mimetype="application/xml",
            headers={"Content-Disposition": "attachment; filename=weather_export.xml"},
        )

    elif format_type in ("markdown", "md"):
        content = export_markdown(record_dicts)
        return Response(
            content,
            mimetype="text/markdown",
            headers={"Content-Disposition": "attachment; filename=weather_export.md"},
        )

    elif format_type == "pdf":
        content = export_pdf(record_dicts)
        return Response(
            content,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=weather_export.pdf"},
        )


# ===========================================================================
# Run
# ===========================================================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)
