from app.modules.medicines.repositories import MedicineRepository
from app.modules.medicines.schemas import MedicineRead


class MedicineService:
    def __init__(self, repository: MedicineRepository):
        self.repository = repository

    async def search(self, query: str, limit: int) -> list[MedicineRead]:
        medicines = await self.repository.search(query.strip(), limit)
        return [MedicineRead.model_validate(medicine) for medicine in medicines]
