import os
from typing import List, Optional

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
    version="1.1.0",
    description="Bulk-insert scraped business listings and fetch aggregated, filterable counts.",
)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

L = models.Listing


def _filtered(stmt, city: Optional[str], category: Optional[str], source: Optional[str]):
    """Apply the optional city / category / source filters to any SELECT on Listing."""
    if city:
        stmt = stmt.where(L.city == city)
    if category:
        stmt = stmt.where(L.category == category)
    if source:
        stmt = stmt.where(L.source == source)
    return stmt


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
    unique = {}
    for item in payload.listings:
        key = (item.business_name.lower(), (item.address or "").lower(), item.source.lower())
        unique.setdefault(key, item)

    existing = set(
        (n.lower(), (a or "").lower(), s.lower())
        for n, a, s in db.execute(select(L.business_name, L.address, L.source))
    )
    fresh = [v for k, v in unique.items() if k not in existing]

    if fresh:
        db.bulk_insert_mappings(L, [i.model_dump() for i in fresh])
        db.commit()

    return schemas.BulkInsertResponse(
        received=len(payload.listings),
        inserted=len(fresh),
        skipped_duplicates=len(payload.listings) - len(fresh),
    )


# ------------------------------------------------------------ list/search
@app.get("/api/listings", response_model=schemas.ListingsPage, tags=["listings"], summary="Browse listings")
def list_listings(
    city: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = Query(None, max_length=100, description="Search in business name or address"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    base = _filtered(select(L), city, category, source)
    if search:
        base = base.where(
            L.business_name.icontains(search, autoescape=True) | L.address.icontains(search, autoescape=True)
        )
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(
        base.order_by(L.business_name, L.id).limit(page_size).offset((page - 1) * page_size)
    ).all()
    return schemas.ListingsPage(total=total, page=page, page_size=page_size, items=rows)


# ------------------------------------------------------------- dashboard
def _count_by(db: Session, column, city, category, source, limit: Optional[int]):
    stmt = _filtered(
        select(column.label("label"), func.count().label("count")).group_by(column),
        city, category, source,
    ).order_by(func.count().desc(), column)
    if limit:
        stmt = stmt.limit(limit)
    return [{"label": r.label, "count": r.count} for r in db.execute(stmt)]


@app.get("/api/dashboard/city-wise", response_model=List[schemas.CountItem], tags=["dashboard"])
def city_wise(
    category: Optional[str] = None,
    source: Optional[str] = None,
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Listings per city. Optionally narrowed by category and/or source."""
    return _count_by(db, L.city, None, category, source, limit)


@app.get("/api/dashboard/category-wise", response_model=List[schemas.CountItem], tags=["dashboard"])
def category_wise(
    city: Optional[str] = None,
    source: Optional[str] = None,
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Listings per category. Optionally narrowed by city and/or source."""
    return _count_by(db, L.category, city, None, source, limit)


@app.get("/api/dashboard/source-wise", response_model=List[schemas.CountItem], tags=["dashboard"])
def source_wise(
    city: Optional[str] = None,
    category: Optional[str] = None,
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Listings per source. Optionally narrowed by city and/or category."""
    return _count_by(db, L.source, city, category, None, limit)


@app.get("/api/dashboard/summary", response_model=schemas.SummaryResponse, tags=["dashboard"])
def summary(
    city: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = _filtered(
        select(
            func.count(),
            func.count(distinct(L.city)),
            func.count(distinct(L.category)),
            func.count(distinct(L.source)),
            func.count(L.phone),  # COUNT(col) ignores NULLs
        ),
        city, category, source,
    )
    row = db.execute(stmt).one()
    return schemas.SummaryResponse(
        total_listings=row[0],
        total_cities=row[1],
        total_categories=row[2],
        total_sources=row[3],
        with_phone=row[4],
    )