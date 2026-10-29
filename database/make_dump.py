"""
Build database/listing_master_dump.sql (schema + INSERTs) from a listings CSV.

    python database/make_dump.py                                  # data/listings.csv (sample data)
    python database/make_dump.py --csv data/listings_osm.csv      # real OpenStreetMap data

Import it with MySQL Workbench (File > Open SQL Script > Execute) or:
    mysql -u root -p < database/listing_master_dump.sql

The dump DROPs and re-creates listing_master, so importing it replaces any
older data (for example the sample rows) instead of duplicating it.
"""
import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default=str(ROOT / "data" / "listings.csv"))
args = ap.parse_args()

rows = list(csv.DictReader(Path(args.csv).open(encoding="utf-8")))


def q(v):
    if v is None or v == "":
        return "NULL"
    return "'" + v.replace("\\", "\\\\").replace("'", "''") + "'"


schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
schema = schema.replace("CREATE TABLE IF NOT EXISTS listing_master", "DROP TABLE IF EXISTS listing_master;\n\nCREATE TABLE listing_master")

out = ["SET NAMES utf8mb4;", "", schema.rstrip(), "", f"-- Data loaded from {Path(args.csv).name} ({len(rows)} rows)", ""]
cols = "(business_name, category, city, address, phone, source)"
BATCH = 100
for i in range(0, len(rows), BATCH):
    vals = ",\n".join(
        "  ({}, {}, {}, {}, {}, {})".format(
            q(r["business_name"]), q(r["category"]), q(r["city"]),
            q(r["address"]), q(r["phone"]), q(r["source"]),
        )
        for r in rows[i : i + BATCH]
    )
    out.append(f"INSERT IGNORE INTO listing_master {cols} VALUES\n{vals};\n")

(ROOT / "database" / "listing_master_dump.sql").write_text("\n".join(out), encoding="utf-8")
print(f"Wrote dump with {len(rows)} rows from {args.csv}")
