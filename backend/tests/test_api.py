import csv
import os
from pathlib import Path

# Use an in-memory-style SQLite file so tests need no MySQL server.
os.environ["DATABASE_URL"] = "sqlite:///./test_listings.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402

client = TestClient(app)
CSV = Path(__file__).resolve().parents[2] / "data" / "listings.csv"


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _rows():
    with open(CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_bulk_insert_and_idempotency():
    rows = _rows()
    r = client.post("/api/listings/bulk", json={"listings": rows})
    assert r.status_code == 201
    assert r.json()["inserted"] == len(rows) >= 500
    # second run inserts nothing
    r2 = client.post("/api/listings/bulk", json={"listings": rows})
    assert r2.json()["inserted"] == 0
    assert r2.json()["skipped_duplicates"] == len(rows)


def test_aggregations_sum_to_total():
    rows = _rows()
    client.post("/api/listings/bulk", json={"listings": rows})
    for path in ("city-wise", "category-wise", "source-wise"):
        data = client.get(f"/api/dashboard/{path}").json()
        assert sum(d["count"] for d in data) == len(rows)
    s = client.get("/api/dashboard/summary").json()
    assert s["total_listings"] == len(rows)
    assert s["with_phone"] == sum(1 for r in rows if r["phone"])


def test_validation_rejects_bad_payload():
    assert client.post("/api/listings/bulk", json={"listings": []}).status_code == 422
    bad = {"listings": [{"business_name": "", "category": "x", "city": "y", "source": "z"}]}
    assert client.post("/api/listings/bulk", json=bad).status_code == 422
