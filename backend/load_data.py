"""
Load a CSV of listings into MySQL through the FastAPI bulk-insert endpoint.

    python load_data.py                       # uses ../data/listings.csv
    python load_data.py --csv ../data/scraped_example.csv --api http://localhost:8000
"""
import argparse
import csv
from pathlib import Path

import requests

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "listings.csv"
BATCH = 200

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default=str(DEFAULT_CSV))
ap.add_argument("--api", default="http://localhost:8000")
args = ap.parse_args()

with open(args.csv, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

total_inserted = total_skipped = 0
for i in range(0, len(rows), BATCH):
    chunk = rows[i : i + BATCH]
    r = requests.post(f"{args.api}/api/listings/bulk", json={"listings": chunk}, timeout=60)
    r.raise_for_status()
    res = r.json()
    total_inserted += res["inserted"]
    total_skipped += res["skipped_duplicates"]
    print(f"batch {i // BATCH + 1}: inserted {res['inserted']}, skipped {res['skipped_duplicates']}")

print(f"Done. {total_inserted} inserted, {total_skipped} duplicates skipped, {len(rows)} rows read.")
