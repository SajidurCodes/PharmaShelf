from datetime import datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.sales.models import SaleLine



from sqlalchemy import func, select

from app.modules.inventory.models import Branch, StockBatch
from app.modules.medicines.models import Medicine
from app.modules.sales.schemas import BestSellerFilters, BestSellerRead, SaleCreate

class SaleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def lock_batch(self, batch_id: UUID) -> StockBatch | None:
        statement = (
            select(StockBatch)
            .where(StockBatch.id == batch_id)
            .with_for_update()
        )
        return await self.session.scalar(statement)

    async def insert_once(
        self, data: SaleCreate, sold_at: datetime
    ) -> SaleLine | None:
        statement = (
            insert(SaleLine)
            .values(**data.model_dump(), sold_at=sold_at)
            .on_conflict_do_nothing(index_elements=[SaleLine.id])
            .returning(SaleLine)
        )
        return await self.session.scalar(statement)

    async def get_by_id(self, sale_id: UUID) -> SaleLine | None:
        return await self.session.get(SaleLine, sale_id)
    

    async def best_sellers(
        self,
        filters: BestSellerFilters,
        start: datetime,
        stop: datetime,
    ) -> list[BestSellerRead]:
        units = func.sum(SaleLine.quantity).label("units_sold")
        revenue = func.sum(
            SaleLine.quantity * SaleLine.unit_sale_price
        ).label("revenue_bdt")

        ranking = revenue if filters.rank_by == "revenue" else units

        statement = (
            select(Medicine.sku, Medicine.name, units, revenue)
            .select_from(SaleLine)
            .join(StockBatch, StockBatch.id == SaleLine.batch_id)
            .join(Branch, Branch.id == StockBatch.branch_id)
            .join(Medicine, Medicine.id == StockBatch.medicine_id)
            .where(
                Branch.code == filters.branch_code,
                SaleLine.sold_at >= start,
                SaleLine.sold_at < stop,
            )
            .group_by(Medicine.id, Medicine.sku, Medicine.name)
            .order_by(ranking.desc(), Medicine.sku)
            .limit(filters.limit)
        )

        rows = (await self.session.execute(statement)).mappings()
        return [BestSellerRead.model_validate(row) for row in rows]