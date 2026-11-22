from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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