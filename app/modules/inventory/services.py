
from app.modules.inventory.repositories import InventoryRepository
from app.modules.inventory.schemas import StockReceiptCreate, StockReceiptRead

from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.core.exceptions.errors import NotFoundError
from app.modules.inventory.schemas import (
    AvailabilityRead,
    ExpiryBatchRead,
    ExpiryRescueReport,
)





class InventoryService:

    def __init__(self, repository: InventoryRepository):
        self.repository = repository

    async def get_availability(
        self, sku: str, branch_code: str
    ) -> AvailabilityRead | None:
        today = datetime.now(ZoneInfo("Asia/Dhaka")).date()
        available = await self.repository.get_availability(sku, branch_code, today)

        if available is None:
            return None

        return AvailabilityRead(available=available)


    async def expiry_rescue(self, branch_code: str, days: int) -> ExpiryRescueReport:


        branch = await self.repository.get_branch_by_code(branch_code)

        if branch is None:
            raise NotFoundError(f"Branch '{branch_code}' was not found")

        today = datetime.now(ZoneInfo("Asia/Dhaka")).date()

        cutoff = today + timedelta(days=days)

        rows = await self.repository.expiring_batches(branch, today, cutoff)


        batches = []
        total = Decimal("0.00")

        for batch, sku, medicine_name in rows:

            days_left = (batch.expires_on - today).days

            value = batch.quantity_remaining * batch.unit_cost


            if days_left <= 14:

                urgency = "within_14_days"

                action = "Review this lot today and check supplier return options."

            elif days_left <= 30:

                urgency = "within_30_days"

                action = "Prioritize this lot when fulfilling existing demand."

            else:

                urgency = "within_60_days"

                action = "Review remaining stock before placing the next order."


            batches.append(
                ExpiryBatchRead(
                    batch_id=batch.id,
                    sku=sku,
                    medicine_name=medicine_name,
                    lot_number=batch.lot_number,
                    expires_on=batch.expires_on,
                    days_left=days_left,
                    quantity_remaining=batch.quantity_remaining,
                    at_risk_bdt=value,
                    urgency=urgency,
                    suggested_action=action,
                )
            )

            total += value


        return ExpiryRescueReport(
            branch_code=branch.code,
            as_of=today,
            window_days=days,
            total_at_risk_bdt=total,
            batches=batches,
        )



class StockReceiptService:

    def __init__(self, repository: InventoryRepository):

        self.repository = repository


    async def record(
        self, data: StockReceiptCreate
    ) -> tuple[StockReceiptRead, bool]:
        session = self.repository.session


        try:

            batch, created = await self.repository.receive_stock(data)
            result = StockReceiptRead.model_validate(batch)
            await session.commit()
            return result, created
        
        except Exception:
            await session.rollback()
            raise