from sqlalchemy import Column, DateTime, Index, Integer, String, UniqueConstraint, func

from .database import Base


class Listing(Base):
    __tablename__ = "listing_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_name = Column(String(255), nullable=False)
    category = Column(String(120), nullable=False)
    city = Column(String(100), nullable=False)
    address = Column(String(500), nullable=True)
    phone = Column(String(30), nullable=True)
    source = Column(String(80), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        # No address prefix length here so the model also works on SQLite for tests;
        # the production DDL in database/schema.sql is the source of truth.
        UniqueConstraint("business_name", "address", "source", name="uq_listing"),
        Index("idx_city", "city"),
        Index("idx_category", "category"),
        Index("idx_source", "source"),
    )
