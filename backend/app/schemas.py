from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ListingIn(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=120)
    city: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=30)
    source: str = Field(..., min_length=1, max_length=80)

    @field_validator("business_name", "category", "city", "source", mode="before")
    @classmethod
    def strip_required(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("address", "phone", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v


class BulkInsertRequest(BaseModel):
    listings: List[ListingIn] = Field(..., min_length=1, max_length=5000)


class BulkInsertResponse(BaseModel):
    received: int
    inserted: int
    skipped_duplicates: int


class CountItem(BaseModel):
    label: str
    count: int


class SummaryResponse(BaseModel):
    total_listings: int
    total_cities: int
    total_categories: int
    total_sources: int
    with_phone: int
