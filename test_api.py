"""Test script for Weather App API endpoints."""
import requests
import json

BASE = "http://127.0.0.1:5000"

def test(label, response, extract_fn=None):
    status = response.status_code
    try:
        data = response.json()
    except Exception:
        data = {}
    detail = extract_fn(data) if extract_fn else json.dumps(data)[:120]
    print(f"  [{status}] {label}: {detail}")
    return data

print("=" * 60)
print("Weather App - API Test Suite")
print("=" * 60)

# 1. Homepage
r = requests.get(BASE + "/")
print(f"\n[{r.status_code}] GET / (Homepage) - length={len(r.text)}")

# 2. Current weather
print("\n--- Current Weather ---")
r = requests.get(BASE + "/api/weather/current", params={"q": "New York"})
d = test("Current weather for New York", r,
         lambda d: f"{d.get('weather',{}).get('temperature')} deg, "
                   f"{d.get('weather',{}).get('weather_description')}, "
                   f"AQI={d.get('air_quality',{}).get('aqi')}")

# 3. CREATE
print("\n--- CRUD: CREATE ---")
r = requests.post(BASE + "/api/weather", json={
    "location": "London",
    "date_start": "2026-11-10",
    "date_end": "2026-11-15",
})
d = test("Create London 11/10-11/15", r,
         lambda d: d.get("message", d.get("error", "?")))
rec_id_1 = d.get("record", {}).get("id")

r = requests.post(BASE + "/api/weather", json={
    "location": "Tokyo",
    "date_start": "2026-11-01",
    "date_end": "2026-11-05",
})
d = test("Create Tokyo 11/01-11/05", r,
         lambda d: d.get("message", d.get("error", "?")))
rec_id_2 = d.get("record", {}).get("id")

# 4. READ
print("\n--- CRUD: READ ---")
r = requests.get(BASE + "/api/weather")
d = test("Read all records", r,
         lambda d: f"{d.get('total',0)} record(s)")

if rec_id_1:
    r = requests.get(BASE + f"/api/weather/{rec_id_1}")
    d = test(f"Read record #{rec_id_1}", r,
             lambda d: f"{d.get('record',{}).get('location_name')} "
                       f"({d.get('record',{}).get('date_start')} to "
                       f"{d.get('record',{}).get('date_end')})")

# 5. UPDATE
print("\n--- CRUD: UPDATE ---")
if rec_id_1:
    r = requests.put(BASE + f"/api/weather/{rec_id_1}", json={
        "location": "Paris",
        "date_start": "2026-11-12",
        "date_end": "2026-11-14",
    })
    d = test(f"Update #{rec_id_1} to Paris", r,
             lambda d: f"{d.get('message', d.get('error', '?'))} -> "
                       f"{d.get('record',{}).get('location_name','?')}")

# 6. Validation tests
print("\n--- Validation ---")
r = requests.post(BASE + "/api/weather", json={
    "location": "Tokyo",
    "date_start": "2026-11-20",
    "date_end": "2026-11-10",
})
test("Bad date range (end < start)", r,
     lambda d: d.get("error", "?"))

r = requests.post(BASE + "/api/weather", json={
    "location": "xyznonexistent12345random",
    "date_start": "2026-11-10",
    "date_end": "2026-11-12",
})
test("Invalid location", r,
     lambda d: d.get("error", "?")[:80])

r = requests.post(BASE + "/api/weather", json={
    "location": "Berlin",
    "date_start": "not-a-date",
    "date_end": "2026-11-12",
})
test("Invalid date format", r,
     lambda d: d.get("error", "?"))

r = requests.post(BASE + "/api/weather", json={})
test("Missing required fields", r,
     lambda d: d.get("error", "?"))

# 7. DELETE
print("\n--- CRUD: DELETE ---")
if rec_id_2:
    r = requests.delete(BASE + f"/api/weather/{rec_id_2}")
    test(f"Delete record #{rec_id_2}", r,
         lambda d: d.get("message", d.get("error", "?")))

r = requests.delete(BASE + "/api/weather/99999")
test("Delete non-existent record", r,
     lambda d: d.get("error", "?"))

# 8. Verify READ after operations
print("\n--- Final State ---")
r = requests.get(BASE + "/api/weather")
d = test("Read all after CRUD ops", r,
         lambda d: f"{d.get('total',0)} record(s) remaining")

# 9. Export tests
print("\n--- Export ---")
for fmt in ["json", "csv", "xml", "markdown", "pdf"]:
    r = requests.get(BASE + f"/api/export/{fmt}")
    ctype = r.headers.get("Content-Type", "")
    test(f"Export {fmt.upper()}", r if r.status_code != 200 else type('R', (), {'status_code': 200, 'json': lambda: {'size': len(r.content)}})(),
         lambda d: f"OK, {d.get('size',0)} bytes" if d.get('size') else "downloaded")
    print(f"      Content-Type: {ctype[:50]}, Size: {len(r.content)} bytes")

# 10. Integrations
print("\n--- Integrations ---")
r = requests.get(BASE + "/api/integrations/wikipedia", params={"q": "Paris"})
d = test("Wikipedia: Paris", r,
         lambda d: f"found={d.get('found')} title={d.get('title','?')}")

r = requests.get(BASE + "/api/integrations/country", params={"code": "FR"})
d = test("Country: FR", r,
         lambda d: f"{d.get('country',{}).get('name','?')} pop={d.get('country',{}).get('population','?')}")

r = requests.get(BASE + "/api/integrations/youtube", params={"q": "Paris"})
d = test("YouTube: Paris", r,
         lambda d: f"source={d.get('source','?')} videos={len(d.get('videos',[]))}")

r = requests.get(BASE + "/api/geocode", params={"q": "10001"})
d = test("Geocode ZIP 10001", r,
         lambda d: f"{d.get('location',{}).get('name','?')} "
                   f"({d.get('location',{}).get('latitude','?')}, "
                   f"{d.get('location',{}).get('longitude','?')})")

r = requests.get(BASE + "/api/geocode", params={"q": "48.8566,2.3522"})
d = test("Geocode GPS coords", r,
         lambda d: f"{d.get('location',{}).get('name','?')}")

r = requests.get(BASE + "/api/geocode", params={"q": "Statue of Liberty"})
d = test("Geocode landmark", r,
         lambda d: f"{d.get('location',{}).get('name','?')}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
