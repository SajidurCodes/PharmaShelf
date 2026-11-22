from app.modules.inventory.services import InventoryService
from app.modules.medicines.services import MedicineService


class CustomerCatalogTools:
    def __init__(
        self,
        medicine_service: MedicineService,
        inventory_service: InventoryService,
    ):
        self.medicine_service = medicine_service
        self.inventory_service = inventory_service

    async def search_medicines(self, query: str) -> dict:
        """Find up to five catalog matches by name, generic name, or SKU."""
        query = query.strip()
        if not query:
            return {"matches": []}

        medicines = await self.medicine_service.search(query, limit=5)
        return {
            "matches": [
                {
                    "sku": medicine.sku,
                    "name": medicine.name,
                    "strength": medicine.strength,
                    "dosage_form": medicine.dosage_form,
                }
                for medicine in medicines
            ]
        }

    async def check_availability(self, sku: str, branch_code: str) -> dict:
        """Check availability of one exact medicine SKU at one branch."""
        result = await self.inventory_service.get_availability(sku, branch_code)
        if result is None:
            return {"status": "unknown_medicine_or_branch"}

        return {
            "sku": sku,
            "branch_code": branch_code,
            "available": result.available,
        }