"""
Collect REAL business listings from OpenStreetMap (Overpass API).

Why OpenStreetMap?
------------------
Justdial / Sulekha / Google Maps forbid scraping in their Terms of Service.
OpenStreetMap is open data (ODbL licence) with a public query API (Overpass)
that is meant to be queried, so this is a compliant source of real businesses:
name, category, address, phone. Attribution: (c) OpenStreetMap contributors.

Polite usage (Overpass fair-use policy): one query per city, a pause between
queries, an identifying User-Agent, retry with back-off on 429/504.

Usage (run on YOUR machine - needs internet):
    python osm_collector.py                       # all default cities -> ../data/listings_osm.csv
    python osm_collector.py --cities Meerut Delhi --per-city 120
    python osm_collector.py --ratio 0.1 --fresh       # different count per city (10% of real count, 100-600)
    python osm_collector.py --contact your.email@gmail.com
    python osm_collector.py --endpoint https://overpass.kumi.systems/api/interpreter

Data quality rules
------------------
* Only elements that have a `name` tag are kept.
* Address comes from addr:* tags. If a place has none, the address is
  "Near <lat>, <lon>, <City>" (real coordinates from OSM, nothing invented).
* Phone is left empty when OSM has none.
* Within each city, listings with a phone/address are preferred.
"""
import argparse
import csv
import re
import time
from pathlib import Path

import requests

DEFAULT_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
USER_AGENT_TEMPLATE = "ListingsDashboardInternAssignment/1.0 (educational project; contact: {contact})"
SOURCE = "OpenStreetMap"

# city -> (south, west, north, east)
CITIES = {
    "Meerut": (28.93, 77.62, 29.05, 77.78),
    "Delhi": (28.50, 77.05, 28.75, 77.35),
    "Mumbai": (18.89, 72.77, 19.25, 72.99),
    "Bengaluru": (12.85, 77.50, 13.10, 77.75),
    "Hyderabad": (17.30, 78.35, 17.55, 78.60),
    "Chennai": (12.95, 80.15, 13.15, 80.30),
    "Kolkata": (22.48, 88.28, 22.65, 88.45),
    "Pune": (18.45, 73.75, 18.62, 73.95),
    "Jaipur": (26.82, 75.72, 27.00, 75.88),
    "Lucknow": (26.78, 80.88, 26.95, 81.05),
    "Ahmedabad": (22.95, 72.50, 23.10, 72.68),
    "Chandigarh": (30.68, 76.70, 30.78, 76.82),
}

# (OSM key, value) -> dashboard category
CATEGORY_MAP = {
    ("amenity", "restaurant"): "Restaurants",
    ("amenity", "fast_food"): "Restaurants",
    ("amenity", "cafe"): "Cafes & Bakeries",
    ("shop", "bakery"): "Cafes & Bakeries",
    ("amenity", "hospital"): "Hospitals & Clinics",
    ("amenity", "clinic"): "Hospitals & Clinics",
    ("amenity", "doctors"): "Hospitals & Clinics",
    ("amenity", "dentist"): "Hospitals & Clinics",
    ("amenity", "pharmacy"): "Pharmacies",
    ("amenity", "school"): "Education & Coaching",
    ("amenity", "college"): "Education & Coaching",
    ("amenity", "university"): "Education & Coaching",
    ("amenity", "language_school"): "Education & Coaching",
    ("amenity", "bank"): "Banks",
    ("tourism", "hotel"): "Hotels & Lodging",
    ("tourism", "guest_house"): "Hotels & Lodging",
    ("shop", "supermarket"): "Grocery & Supermarkets",
    ("shop", "convenience"): "Grocery & Supermarkets",
    ("shop", "greengrocer"): "Grocery & Supermarkets",
    ("shop", "clothes"): "Clothing & Boutiques",
    ("shop", "boutique"): "Clothing & Boutiques",
    ("shop", "electronics"): "Electronics & Repair",
    ("shop", "mobile_phone"): "Electronics & Repair",
    ("shop", "computer"): "Electronics & Repair",
    ("shop", "hairdresser"): "Salons & Spas",
    ("shop", "beauty"): "Salons & Spas",
    ("leisure", "fitness_centre"): "Gyms & Fitness",
    ("shop", "car_repair"): "Auto Services",
    ("shop", "car"): "Auto Services",
    ("shop", "motorcycle"): "Auto Services",
    ("amenity", "fuel"): "Fuel Stations",
}

COLUMNS = ["business_name", "category", "city", "address", "phone", "source"]


def build_query(bbox, timeout=90):
    s, w, n, e = bbox
    by_key = {}
    for (k, v) in CATEGORY_MAP:
        by_key.setdefault(k, []).append(v)
    parts = []
    for k, values in by_key.items():
        regex = "|".join(values)
        parts.append(f'  nwr["name"]["{k}"~"^({regex})$"]({s},{w},{n},{e});')
    return f"[out:json][timeout:{timeout}];\n(\n" + "\n".join(parts) + "\n);\nout center tags;"


def category_of(tags):
    for (k, v), cat in CATEGORY_MAP.items():
        if tags.get(k) == v:
            return cat
    return None


def clean_phone(tags):
    raw = tags.get("phone") or tags.get("contact:phone") or tags.get("mobile") or tags.get("contact:mobile") or ""
    first = re.split(r"[;,/]", raw)[0].strip()
    return first[:30]


def build_address(tags, city, lat, lon):
    if tags.get("addr:full"):
        return tags["addr:full"][:500]
    bits = [
        " ".join(x for x in [tags.get("addr:housenumber"), tags.get("addr:street")] if x),
        tags.get("addr:suburb") or tags.get("addr:neighbourhood") or tags.get("addr:place"),
        tags.get("addr:city") or None,
        tags.get("addr:postcode"),
    ]
    bits = [b for b in bits if b]
    if bits:
        text = ", ".join(bits)
        return text if city.lower() in text.lower() else f"{text}, {city}"
    if lat is not None and lon is not None:
        return f"Near {lat:.5f}, {lon:.5f}, {city}"
    return city


def parse_elements(elements, city):
    """Overpass elements -> list of row dicts (deduped, best-quality first)."""
    rows, seen = [], set()
    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name") or "").strip()
        category = category_of(tags)
        if not name or not category:
            continue
        lat = el.get("lat", (el.get("center") or {}).get("lat"))
        lon = el.get("lon", (el.get("center") or {}).get("lon"))
        row = {
            "business_name": name[:255],
            "category": category,
            "city": city,
            "address": build_address(tags, city, lat, lon),
            "phone": clean_phone(tags),
            "source": SOURCE,
        }
        key = (row["business_name"].lower(), row["address"].lower())
        if key in seen:
            continue
        seen.add(key)
        # completeness score: real phone and real street address rank first
        row["_score"] = (2 if row["phone"] else 0) + (1 if not row["address"].startswith("Near ") else 0)
        rows.append(row)
    rows.sort(key=lambda r: -r["_score"])
    return rows


def fetch_city(endpoints, bbox, user_agent, retries=3):
    """Try each Overpass server in turn; back off when a server is busy."""
    query = build_query(bbox)
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    for endpoint in endpoints:
        delay = 15
        for attempt in range(1, retries + 1):
            try:
                resp = requests.post(endpoint, data={"data": query}, headers=headers, timeout=180)
            except requests.RequestException as exc:
                print(f"  {endpoint} unreachable ({exc.__class__.__name__}); trying next server")
                break
            if resp.status_code == 200:
                return resp.json().get("elements", [])
            if resp.status_code in (429, 502, 503, 504):
                print(f"  server busy ({resp.status_code}); waiting {delay}s (attempt {attempt}/{retries})")
                time.sleep(delay)
                delay *= 2
                continue
            print(f"  {endpoint} answered {resp.status_code}; trying next server")
            break
    raise RuntimeError("All Overpass servers refused or were busy; wait a few minutes and run again.")


def load_existing(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def pick_cap(found, args):
    """How many listings to keep for a city that has `found` real listings in OSM.

    --ratio keeps a share of the real count (clamped between --min-per-city and
    --max-per-city), so bigger cities keep more rows than smaller ones.
    Without --ratio a fixed --per-city cap is used.
    """
    if args.ratio:
        return max(args.min_per_city, min(args.max_per_city, round(found * args.ratio)))
    return args.per_city


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", nargs="*", default=list(CITIES), help="subset of: " + ", ".join(CITIES))
    ap.add_argument("--per-city", type=int, default=90, help="max listings kept per city")
    ap.add_argument("--ratio", type=float, default=None, help="keep this share of each city's real count, e.g. 0.1 = 10%% (overrides --per-city)")
    ap.add_argument("--min-per-city", type=int, default=100, help="lower bound when using --ratio")
    ap.add_argument("--max-per-city", type=int, default=600, help="upper bound when using --ratio")
    ap.add_argument("--endpoint", default=None, help="use one specific Overpass server instead of the built-in list")
    ap.add_argument("--contact", default="student assignment", help="your email, put in the User-Agent (Overpass asks for an identifiable client)")
    ap.add_argument("--pause", type=int, default=12, help="seconds to wait between city queries")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data" / "listings_osm.csv"))
    ap.add_argument("--fresh", action="store_true", help="ignore an existing output file and start over")
    args = ap.parse_args()

    endpoints = [args.endpoint] if args.endpoint else DEFAULT_ENDPOINTS
    user_agent = USER_AGENT_TEMPLATE.format(contact=args.contact)
    out = Path(args.out)

    # Resume support: keep cities already saved, only fetch the missing ones.
    all_rows = [] if args.fresh else load_existing(out)
    done = {r["city"] for r in all_rows}
    if done:
        print(f"Resuming: {len(all_rows)} rows already saved for {sorted(done)}")

    todo = [c for c in args.cities if c not in done]
    failed = []
    for i, city in enumerate(todo):
        if city not in CITIES:
            print(f"Unknown city {city!r}, skipping")
            continue
        print(f"[{i + 1}/{len(todo)}] {city} ...")
        try:
            found = parse_elements(fetch_city(endpoints, CITIES[city], user_agent), city)
            rows = found[: pick_cap(len(found), args)]
        except RuntimeError as exc:
            print(f"  FAILED {city}: {exc}")
            failed.append(city)
            continue
        print(f"  found {len(found)} in OSM, kept {len(rows)} ({sum(1 for r in rows if r['phone'])} with phone)")
        all_rows.extend(rows)
        save(out, all_rows)  # save after every city so nothing is lost
        if i < len(todo) - 1:
            time.sleep(args.pause)

    save(out, all_rows)
    print(f"\nSaved {len(all_rows)} real listings to {out}")
    if failed:
        print(f"Could not fetch: {', '.join(failed)}. Run the same command again in a few minutes; finished cities are skipped.")
    if len(all_rows) < 500:
        print("Fewer than 500 rows: run again for the missing cities or raise --per-city.")


if __name__ == "__main__":
    main()
