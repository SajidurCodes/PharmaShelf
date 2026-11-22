from app.modules.medicines.repositories import MedicineRepository
from app.core.exceptions.errors import ConflictError
from app.modules.medicines.schemas import MedicineCreate, MedicineRead, MedicineUpdate
from app.core.exceptions.errors import ConflictError, NotFoundError


class MedicineService:
    def __init__(self, repository: MedicineRepository):
        self.repository = repository

    async def search(self, query: str, limit: int) -> list[MedicineRead]:
        medicines = await self.repository.search(query.strip(), limit)
        return [MedicineRead.model_validate(medicine) for medicine in medicines]

    async def create(self, data: MedicineCreate) -> MedicineRead:
        medicine = await self.repository.create(data)
        if medicine is None:
            raise ConflictError(f"Medicine with SKU '{data.sku}' already exists")

        return MedicineRead.model_validate(medicine)
    async def get_by_sku(self, sku: str) -> MedicineRead:
        medicine = await self.repository.get_by_sku(sku)
        if medicine is None:
            raise NotFoundError(f"Medicine with SKU '{sku}' was not found")

        return MedicineRead.model_validate(medicine)

    async def update_by_sku(self, sku: str, data: MedicineUpdate) -> MedicineRead:
        medicine = await self.repository.update_by_sku(sku, data)
        if medicine is None:
            raise NotFoundError(f"Medicine with SKU '{sku}' was not found")

        return MedicineRead.model_validate(medicine)


    async def delete_by_sku(self, sku: str) -> None:
        deleted = await self.repository.delete_by_sku(sku)
        if not deleted:
            raise NotFoundError(f"Medicine with SKU '{sku}' was not found")