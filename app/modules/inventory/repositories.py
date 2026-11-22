from datetime import date

from sqlalchemy import  true
from sqlalchemy.ext.asyncio import AsyncSession





from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.exceptions.errors import ConflictError, NotFoundError
from app.modules.inventory.models import Branch, StockBatch
from app.modules.inventory.schemas import StockReceiptCreate
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
    

    async def get_branch_by_code(self, branch_code: str) -> Branch | None:
        statement = select(Branch).where(Branch.code == branch_code)
        return await self.session.scalar(statement)

    async def expiring_batches(self, branch: Branch, today: date, cutoff: date):
        statement = (
            select(StockBatch, Medicine.sku, Medicine.name)
            .join(Medicine, Medicine.id == StockBatch.medicine_id)
            .where(
                StockBatch.branch_id == branch.id,
                StockBatch.quantity_remaining > 0,
                StockBatch.received_on <= today,
                StockBatch.expires_on > today,
                StockBatch.expires_on <= cutoff,
            )
            .order_by(StockBatch.expires_on, Medicine.sku, StockBatch.id)
        )
        result = await self.session.execute(statement)
        return result.all()



    async def receive_stock(
        self, data: StockReceiptCreate
    ) -> tuple[StockBatch, bool]:
        branch_id = await self.session.scalar(
            select(Branch.id).where(Branch.code == data.branch_code)
        )
        if branch_id is None:
            raise NotFoundError("Branch was not found")

        medicine_id = await self.session.scalar(
            select(Medicine.id).where(Medicine.sku == data.sku)
        )
        if medicine_id is None:
            raise NotFoundError("Medicine was not found")

        receipt = {
            "id": data.id,
            "branch_id": branch_id,
            "medicine_id": medicine_id,
            "lot_number": data.lot_number,
            "received_on": data.received_on,
            "expires_on": data.expires_on,
            "quantity_received": data.quantity_received,
            "unit_cost": data.unit_cost,
        }

        statement = (
            insert(StockBatch)
            .values(**receipt, quantity_remaining=data.quantity_received)
            .on_conflict_do_nothing(index_elements=[StockBatch.id])
            .returning(StockBatch)
        )
        batch = await self.session.scalar(statement)
        if batch is not None:
            return batch, True

        existing = await self.session.get(StockBatch, data.id)
        if existing is None or any(
            getattr(existing, field) != value for field, value in receipt.items()
        ):
            raise ConflictError("This receipt ID was used for a different delivery")

        return existing, False