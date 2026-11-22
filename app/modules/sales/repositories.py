from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.models import StockBatch
from app.modules.sales.models import SaleLine
from app.modules.sales.schemas import SaleCreate


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