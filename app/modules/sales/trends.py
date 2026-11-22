from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.errors import NotFoundError
from app.modules.inventory.models import Branch, StockBatch
from app.modules.medicines.models import Medicine
from app.modules.sales.models import SaleLine


class DailyDemand(BaseModel):
    day: date
    units: int
    revenue_bdt: Decimal


class DemandTrend(BaseModel):
    branch_code: str
    sku: str
    medicine_name: str
    start_date: date
    end_date: date
    previous_start: date
    previous_end: date
    units: int
    previous_units: int
    change_units: int
    change_percent: Decimal | None
    revenue_bdt: Decimal
    previous_revenue_bdt: Decimal
    days: list[DailyDemand]


async def daily_sales(
    session: AsyncSession,
    branch_id: UUID,
    medicine_id: UUID,
    start: datetime,
    stop: datetime,
) -> dict[date, DailyDemand]:
    local_day = cast(func.timezone("Asia/Dhaka", SaleLine.sold_at), Date)

    statement = (
        select(
            local_day.label("day"),
            func.sum(SaleLine.quantity).label("units"),
            func.sum(SaleLine.quantity * SaleLine.unit_sale_price).label("revenue_bdt"),
        )
        .select_from(SaleLine)
        .join(StockBatch, StockBatch.id == SaleLine.batch_id)
        .where(
            StockBatch.branch_id == branch_id,
            StockBatch.medicine_id == medicine_id,
            SaleLine.sold_at >= start,
            SaleLine.sold_at < stop,
        )
        .group_by(local_day)
    )
    rows = (await session.execute(statement)).mappings()
    return {row["day"]: DailyDemand.model_validate(row) for row in rows}


async def get_demand_trend(
    session: AsyncSession,
    branch_code: str,
    sku: str,
    start_date: date,
    end_date: date,
) -> DemandTrend:
    length = (end_date - start_date).days + 1
    if not 1 <= length <= 366:
        raise ValueError("Choose a period between 1 and 366 days")
    if start_date.toordinal() <= length or end_date == date.max:
        raise ValueError("Choose dates that allow a preceding comparison period")

    branch_id = await session.scalar(select(Branch.id).where(Branch.code == branch_code))
    if branch_id is None:
        raise NotFoundError("Branch was not found")

    medicine = await session.scalar(select(Medicine).where(Medicine.sku == sku))
    if medicine is None:
        raise NotFoundError("Medicine was not found")

    previous_start = start_date - timedelta(days=length)
    previous_end = start_date - timedelta(days=1)
    dhaka = ZoneInfo("Asia/Dhaka")

    daily = await daily_sales(
        session,
        branch_id,
        medicine.id,
        datetime.combine(previous_start, time.min, tzinfo=dhaka),
        datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=dhaka),
    )

    days = []
    for offset in range(length):
        day = start_date + timedelta(days=offset)
        days.append(daily.get(day) or DailyDemand(day=day, units=0, revenue_bdt=Decimal("0.00")))

    previous = [entry for day, entry in daily.items() if day < start_date]
    units = sum(entry.units for entry in days)
    previous_units = sum(entry.units for entry in previous)
    change = units - previous_units
    percent = None
    if previous_units:
        percent = (Decimal(change) * 100 / previous_units).quantize(Decimal("0.1"))

    return DemandTrend(
        branch_code=branch_code,
        sku=sku,
        medicine_name=medicine.name,
        start_date=start_date,
        end_date=end_date,
        previous_start=previous_start,
        previous_end=previous_end,
        units=units,
        previous_units=previous_units,
        change_units=change,
        change_percent=percent,
        revenue_bdt=sum((entry.revenue_bdt for entry in days), Decimal("0.00")),
        previous_revenue_bdt=sum((entry.revenue_bdt for entry in previous), Decimal("0.00")),
        days=days,
    )