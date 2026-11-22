from datetime import datetime
from zoneinfo import ZoneInfo

from app.modules.inventory.repositories import InventoryRepository
from app.modules.inventory.schemas import AvailabilityRead


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