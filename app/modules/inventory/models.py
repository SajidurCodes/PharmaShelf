from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(160))




class StockBatch(Base):

    __tablename__ = "stock_batches"

    __table_args__ = (
        CheckConstraint("quantity_received > 0", name="ck_batch_received_positive"),
        CheckConstraint(
            "quantity_remaining BETWEEN 0 AND quantity_received",
            name="ck_batch_remaining_range",
        ),
        CheckConstraint("unit_cost >= 0", name="ck_batch_unit_cost_nonnegative"),
    )


    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    medicine_id: Mapped[UUID] = mapped_column(
        ForeignKey("medicines.id"), index=True
    )
    
    branch_id: Mapped[UUID] = mapped_column(
        ForeignKey("branches.id"), index=True
    )
    lot_number: Mapped[str] = mapped_column(String(80))
    received_on: Mapped[date]
    expires_on: Mapped[date] = mapped_column(index=True)
    quantity_received: Mapped[int]
    quantity_remaining: Mapped[int]
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))