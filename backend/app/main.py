import os
from typing import List

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

# Creates the table if it doesn't exist yet (schema.sql does the same, with a prefix index).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Business Listings Dashboard API",
    version="1.0.0",
    description="Bulk-insert scraped business listings and fetch aggregated counts.",
)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------- insert
@app.post(
    "/api/listings/bulk",
    response_model=schemas.BulkInsertResponse,
    status_code=201,
    tags=["listings"],
    summary="Bulk insert scraped listings",
)
def bulk_insert(payload: schemas.BulkInsertRequest, db: Session = Depends(get_db)):
    """Insert many listings in one transaction. Rows that already exist
    (same business_name + address + source) are skipped, so re-running the
    loader is safe."""
    # Dedupe inside the request first.
    unique = {}
    for item in payload.listings:
        key = (item.business_name.lower(), (item.address or "").lower(), item.source.lower())
        unique.setdefault(key, item)

    # Find which of them already exist in the DB.
    existing = set(
        (n.lower(), (a or "").lower(), s.lower())
        for n, a, s in db.execute(
            select(models.Listing.business_name, models.Listing.address, models.Listing.source)
        )
    )
    fresh = [v for k, v in unique.items() if k not in existing]

    if fresh:
        db.bulk_insert_mappings(models.Listing, [i.model_dump() for i in fresh])
        db.commit()

    return schemas.BulkInsertResponse(
        received=len(payload.listings),
        inserted=len(fresh),
        skipped_duplicates=len(payload.listings) - len(fresh),
    )


# ------------------------------------------------------------- dashboard
def _count_by(db: Session, column, limit: int | None):
    stmt = (
        select(column.label("label"), func.count().label("count"))
        .group_by(column)
        .order_by(func.count().desc(), column)
    )
    if limit:
        stmt = stmt.limit(limit)
    return [{"label": r.label, "count": r.count} for r in db.execute(stmt)]


@app.get("/api/dashboard/city-wise", response_model=List[schemas.CountItem], tags=["dashboard"])
def city_wise(limit: int | None = Query(None, ge=1, le=100), db: Session = Depends(get_db)):
    return _count_by(db, models.Listing.city, limit)


@app.get("/api/dashboard/category-wise", response_model=List[schemas.CountItem], tags=["dashboard"])
def category_wise(limit: int | None = Query(None, ge=1, le=100), db: Session = Depends(get_db)):
    return _count_by(db, models.Listing.category, limit)


@app.get("/api/dashboard/source-wise", response_model=List[schemas.CountItem], tags=["dashboard"])
def source_wise(limit: int | None = Query(None, ge=1, le=100), db: Session = Depends(get_db)):
    return _count_by(db, models.Listing.source, limit)


@app.get("/api/dashboard/summary", response_model=schemas.SummaryResponse, tags=["dashboard"])
def summary(db: Session = Depends(get_db)):
    L = models.Listing
    row = db.execute(
        select(
            func.count(),
            func.count(distinct(L.city)),
            func.count(distinct(L.category)),
            func.count(distinct(L.source)),
            func.count(L.phone),  # COUNT(col) ignores NULLs
        )
    ).one()
    return schemas.SummaryResponse(
        total_listings=row[0],
        total_cities=row[1],
        total_categories=row[2],
        total_sources=row[3],
        with_phone=row[4],
    )
