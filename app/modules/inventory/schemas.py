from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


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