from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SaleLine(Base):

    __tablename__ = "sale_lines"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_line_quantity_positive"),
        CheckConstraint(
            "unit_sale_price >= 0",
            name="ck_sale_line_price_nonnegative",
        ),
    )
    

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("stock_batches.id"), index=True
    )
    sold_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
    quantity: Mapped[int]
    unit_sale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))