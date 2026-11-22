from datetime import date

from sqlalchemy import select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.models import Branch, StockBatch
from app.modules.medicines.models import Medicine


class InventoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_availability(
        self, sku: str, branch_code: str, today: date
    ) -> bool | None:
        available_batch = (
            select(StockBatch.id)
            .where(
                StockBatch.medicine_id == Medicine.id,
                StockBatch.branch_id == Branch.id,
                StockBatch.quantity_remaining > 0,
                StockBatch.expires_on > today,
                StockBatch.received_on <= today,
            )
            .correlate(Medicine, Branch)
            .exists()
        )

        statement = (
            select(available_batch)
            .select_from(Medicine)
            .join(Branch, true())
            .where(Medicine.sku == sku, Branch.code == branch_code)
        )

        return await self.session.scalar(statement)