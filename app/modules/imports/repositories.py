from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.models import StockBatch
from app.modules.sales.models import SaleLine


class ImportRepository:


    def __init__(self, session: AsyncSession):

        self.session =session

    async def existing_batch_ids(self, ids: set[UUID]) -> set[UUID]:

        statement =select(StockBatch.id).where(StockBatch.id.in_(ids))
        result =await self.session.scalars(statement)
        return set(result)

    async def existing_sale_ids(self, ids: set[UUID]) -> set[UUID]:


        statement =select(SaleLine.id).where(SaleLine.id.in_(ids))
        result= await self.session.scalars(statement)
        return set(result)