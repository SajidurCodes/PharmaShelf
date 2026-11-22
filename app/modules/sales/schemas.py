from datetime import datetime
from decimal import Decimal
from uuid import UUID

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SaleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    batch_id: UUID
    quantity: int = Field(gt=0, le=2_147_483_647)
    unit_sale_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class SaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    sold_at: datetime
    quantity: int
    unit_sale_price: Decimal


class BestSellerFilters(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    branch_code: str = Field(min_length=1, max_length=40)
    start_date: date
    end_date: date
    rank_by: Literal["units", "revenue"] = "units"
    limit: int = Field(default=10, ge=1, le=50)

    @model_validator(mode="after")
    def validate_period(self) -> "BestSellerFilters":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.end_date == date.max:
            raise ValueError("end_date must be earlier than 9999-12-31")
        return self


class BestSellerRead(BaseModel):
    sku: str
    name: str
    units_sold: int
    revenue_bdt: Decimal