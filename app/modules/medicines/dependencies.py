from typing import Annotated

from fastapi import Depends

from app.db.session import SessionDep
from app.modules.medicines.repositories import MedicineRepository
from app.modules.medicines.services import MedicineService


def get_medicine_service(session: SessionDep) -> MedicineService:
    repository = MedicineRepository(session)
    return MedicineService(repository)


MedicineServiceDep = Annotated[MedicineService, Depends(get_medicine_service)]