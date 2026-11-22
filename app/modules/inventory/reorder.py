from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.errors import NotFoundError
from app.modules.inventory.models import Branch, StockBatch
from app.modules.medicines.models import Medicine
from app.modules.sales.models import SaleLine


DHAKA = ZoneInfo("Asia/Dhaka")
SALES_WINDOW_DAYS = 30
DEAD_STOCK_DAYS = 60
LOW_STOCK_DAYS = 7

StockStatus = Literal[
    "out_of_stock",
    "running_low",
    "dead_stock",
    "no_recent_sales",
    "in_stock",
]

STATUS_ORDER = {
    "out_of_stock": 0,
    "running_low": 1,
    "dead_stock": 2,
    "no_recent_sales": 3,
    "in_stock": 4,
}


class ReorderItem(BaseModel):
    sku: str
    medicine_name: str
    usable_units: int
    units_sold_30d: int
    days_left: Decimal | None
    status: StockStatus
    suggested_action: str


class ReorderReport(BaseModel):
    branch_code: str
    as_of: date
    sales_window_start: date
    sales_window_end: date
    low_stock_days: int
    items: list[ReorderItem]


def assess_stock(
    usable_units: int,
    units_sold_30d: int,
    units_sold_60d: int,
    first_received: date,
    history_start: date,
) -> tuple[StockStatus, Decimal | None, str]:
    days_left = None

    if units_sold_30d > 0:
        days_left = (
            Decimal(usable_units) * SALES_WINDOW_DAYS / units_sold_30d
        ).quantize(Decimal("0.1"))

    if usable_units == 0:
        action = (
            "Review recent sales and supplier lead time before placing a reorder."
            if units_sold_30d > 0
            else "Check whether this branch still needs to carry this medicine."
        )
        return "out_of_stock", days_left, action

    if first_received <= history_start and units_sold_60d == 0:
        return (
            "dead_stock",
            None,
            "Pause reordering and review expiry dates and supplier return options.",
        )

    if units_sold_30d == 0:
        return (
            "no_recent_sales",
            None,
            "Review sales history before deciding how much to reorder.",
        )

    # Compare before rounding so 7.04 days does not trigger a 7-day alert.
    if usable_units * SALES_WINDOW_DAYS <= units_sold_30d * LOW_STOCK_DAYS:
        return (
            "running_low",
            days_left,
            "Check the next delivery date. Current stock covers a week or less.",
        )

    return "in_stock", days_left, "Continue monitoring stock and sales."


async def get_reorder_report(
    session: AsyncSession,
    branch_code: str,
) -> ReorderReport:
    today = datetime.now(DHAKA).date()
    sales_start = today - timedelta(days=SALES_WINDOW_DAYS)
    history_start = today - timedelta(days=DEAD_STOCK_DAYS)

    branch_id = await session.scalar(
        select(Branch.id).where(Branch.code == branch_code)
    )
    if branch_id is None:
        raise NotFoundError("Branch was not found")

    # Keep depleted and expired batches in the branch history. Only usable
    # batches contribute to the current balance.
    inventory = (
        select(
            StockBatch.medicine_id,
            func.min(StockBatch.received_on).label("first_received"),
            func.coalesce(
                func.sum(StockBatch.quantity_remaining).filter(
                    StockBatch.expires_on > today
                ),
                0,
            ).label("usable_units"),
        )
        .where(
            StockBatch.branch_id == branch_id,
            StockBatch.received_on <= today,
        )
        .group_by(StockBatch.medicine_id)
        .subquery()
    )

    start_60 = datetime.combine(history_start, time.min, tzinfo=DHAKA)
    start_30 = datetime.combine(sales_start, time.min, tzinfo=DHAKA)
    stop = datetime.combine(today, time.min, tzinfo=DHAKA)

    # Aggregate sales separately so a batch with several sales contributes
    # its remaining balance only once.
    sales = (
        select(
            StockBatch.medicine_id,
            func.sum(SaleLine.quantity).label("units_60d"),
            func.sum(SaleLine.quantity)
            .filter(SaleLine.sold_at >= start_30)
            .label("units_30d"),
        )
        .select_from(SaleLine)
        .join(StockBatch, StockBatch.id == SaleLine.batch_id)
        .where(
            StockBatch.branch_id == branch_id,
            SaleLine.sold_at >= start_60,
            SaleLine.sold_at < stop,
        )
        .group_by(StockBatch.medicine_id)
        .subquery()
    )

    statement = (
        select(
            Medicine.sku,
            Medicine.name,
            inventory.c.first_received,
            inventory.c.usable_units,
            func.coalesce(sales.c.units_30d, 0).label("units_30d"),
            func.coalesce(sales.c.units_60d, 0).label("units_60d"),
        )
        .select_from(inventory)
        .join(Medicine, Medicine.id == inventory.c.medicine_id)
        .outerjoin(sales, sales.c.medicine_id == inventory.c.medicine_id)
    )

    items = []
    for row in (await session.execute(statement)).mappings():
        status, days_left, action = assess_stock(
            usable_units=row["usable_units"],
            units_sold_30d=row["units_30d"],
            units_sold_60d=row["units_60d"],
            first_received=row["first_received"],
            history_start=history_start,
        )

        items.append(
            ReorderItem(
                sku=row["sku"],
                medicine_name=row["name"],
                usable_units=row["usable_units"],
                units_sold_30d=row["units_30d"],
                days_left=days_left,
                status=status,
                suggested_action=action,
            )
        )

    items.sort(
        key=lambda item: (
            STATUS_ORDER[item.status],
            item.days_left if item.days_left is not None else Decimal("Infinity"),
            item.sku,
        )
    )

    return ReorderReport(
        branch_code=branch_code,
        as_of=today,
        sales_window_start=sales_start,
        sales_window_end=today - timedelta(days=1),
        low_stock_days=LOW_STOCK_DAYS,
        items=items,
    )