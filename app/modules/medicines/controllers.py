from typing import Annotated

from fastapi import APIRouter, Query

from app.modules.medicines.dependencies import MedicineServiceDep
from app.modules.medicines.schemas import MedicineRead


router = APIRouter(prefix="/medicines", tags=["Medicines"])


@router.get("", response_model=list[MedicineRead])
async def list_medicines(
    service: MedicineServiceDep,
    q: Annotated[str, Query(max_length=160)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[MedicineRead]:
    return await service.search(q, limit)