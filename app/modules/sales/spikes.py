from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.errors import NotFoundError
from app.modules.inventory.models import Branch, StockBatch
from app.modules.medicines.models import Medicine
from app.modules.sales.models import SaleLine


DHAKA = ZoneInfo("Asia/Dhaka")
WEEK_DAYS = 7
BASELINE_WEEKS = 4
MIN_WEEKLY_UNITS = 5
SPIKE_MULTIPLIER = 2


class DemandSpike(BaseModel):
    sku: str
    medicine_name: str
    recent_units: int
    baseline_units: int
    baseline_weekly_average: Decimal
    multiple: Decimal


class SpikeReport(BaseModel):
    branch_code: str
    recent_start: date
    recent_end: date
    baseline_start: date
    baseline_end: date
    alerts: list[DemandSpike]


async def get_demand_spikes(session: AsyncSession,branch_code: str,) -> SpikeReport:

    
    today = datetime.now(DHAKA).date()

    recent_start = today - timedelta(days=WEEK_DAYS)

    baseline_start = recent_start - timedelta(weeks=BASELINE_WEEKS)


    branch_id = await session.scalar(select(Branch.id).where(Branch.code == branch_code))

    if branch_id is None:

        raise NotFoundError("Branch was not found")

    baseline_at = datetime.combine(baseline_start, time.min, tzinfo=DHAKA)
    recent_at = datetime.combine(recent_start, time.min, tzinfo=DHAKA)
    stop_at = datetime.combine(today, time.min, tzinfo=DHAKA)


    
    established_medicines = (
        select(StockBatch.medicine_id)
        .where(
            StockBatch.branch_id == branch_id,
            StockBatch.received_on <= baseline_start,
        )
        .distinct()
        .subquery()
    )

    recent_units = func.coalesce(
        func.sum(SaleLine.quantity).filter(SaleLine.sold_at >= recent_at),
        0,
    )
    baseline_units = func.coalesce(
        func.sum(SaleLine.quantity).filter(SaleLine.sold_at < recent_at),
        0,
    )

    statement = (
        select(
            Medicine.sku,
            Medicine.name,
            recent_units.label("recent_units"),
            baseline_units.label("baseline_units"),
        )
        .select_from(SaleLine)
        .join(StockBatch, StockBatch.id == SaleLine.batch_id)
        .join(Medicine, Medicine.id == StockBatch.medicine_id)
        .join(
            established_medicines,
            established_medicines.c.medicine_id == Medicine.id,
        )
        .where(
            StockBatch.branch_id == branch_id,
            SaleLine.sold_at >= baseline_at,
            SaleLine.sold_at < stop_at,
        )
        .group_by(Medicine.id, Medicine.sku, Medicine.name)
        .having(
            recent_units >= MIN_WEEKLY_UNITS,
            baseline_units > 0,
            recent_units * BASELINE_WEEKS >= baseline_units * SPIKE_MULTIPLIER,
        )
    )



    rows = (await session.execute(statement)).mappings()
    alerts = []

    for row in rows:

        average = Decimal(row["baseline_units"]) / BASELINE_WEEKS

        multiple = Decimal(row["recent_units"]) / average

        alerts.append(
            DemandSpike(
                sku=row["sku"],
                medicine_name=row["name"],
                recent_units=row["recent_units"],
                baseline_units=row["baseline_units"],
                baseline_weekly_average=average,
                multiple=multiple.quantize(Decimal("0.01")),
            )
        )


    alerts.sort(key=lambda alert: (-alert.multiple, -alert.recent_units, alert.sku))
    

    return SpikeReport(
        branch_code=branch_code,
        recent_start=recent_start,
        recent_end=today - timedelta(days=1),
        baseline_start=baseline_start,
        baseline_end=recent_start - timedelta(days=1),
        alerts=alerts,
    )