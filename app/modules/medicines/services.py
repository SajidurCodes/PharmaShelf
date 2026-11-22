from app.modules.medicines.repositories import MedicineRepository
from app.core.exceptions.errors import ConflictError
from app.modules.medicines.schemas import MedicineCreate, MedicineRead


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
