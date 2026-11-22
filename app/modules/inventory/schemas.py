from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AvailabilityRead(BaseModel):
    available: bool


class ExpiryBatchRead(BaseModel):
    batch_id: UUID
    sku: str
    medicine_name: str
    lot_number: str
    expires_on: date
    days_left: int
    quantity_remaining: int
    at_risk_bdt: Decimal
    urgency: Literal["within_14_days", "within_30_days", "within_60_days"]
    suggested_action: str


class ExpiryRescueReport(BaseModel):
    branch_code: str
    as_of: date
    window_days: int
    total_at_risk_bdt: Decimal
    batches: list[ExpiryBatchRead]


class StockReceiptCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: UUID
    branch_code: str = Field(min_length=1, max_length=40)
    sku: str = Field(min_length=1, max_length=64)
    lot_number: str = Field(min_length=1, max_length=80)
    received_on: date
    expires_on: date
    quantity_received: int = Field(gt=0, le=2_147_483_647)
    unit_cost: Decimal = Field(ge=0, max_digits=12, decimal_places=2)

    @model_validator(mode="after")
    def validate_dates(self) -> "StockReceiptCreate":
        if self.expires_on <= self.received_on:
            raise ValueError("Expiry date must be after the received date")
        return self


class StockReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lot_number: str
    received_on: date
    expires_on: date
    quantity_received: int
    quantity_remaining: int