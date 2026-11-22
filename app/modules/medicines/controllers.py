from typing import Annotated


from app.modules.medicines.dependencies import MedicineServiceDep


from fastapi import APIRouter, Depends, Query, status

from app.modules.auth.dependencies import require_admin
from app.modules.medicines.schemas import MedicineCreate, MedicineRead, MedicineUpdate


router = APIRouter(prefix="/medicines", tags=["Medicines"])


@router.get("", response_model=list[MedicineRead])
async def list_medicines(
    service: MedicineServiceDep,
    q: Annotated[str, Query(max_length=160)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[MedicineRead]:
    return await service.search(q, limit)



@router.post(
    "",
    response_model=MedicineRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_medicine(
    data: MedicineCreate,
    service: MedicineServiceDep,
) -> MedicineRead:
    return await service.create(data)


@router.get("/{sku}", response_model=MedicineRead)
async def get_medicine(sku: str, service: MedicineServiceDep) -> MedicineRead:
    return await service.get_by_sku(sku)


@router.patch(
    "/{sku}",
    response_model=MedicineRead,
    dependencies=[Depends(require_admin)],
)
async def update_medicine(
    sku: str,
    data: MedicineUpdate,
    service: MedicineServiceDep,
) -> MedicineRead:
    return await service.update_by_sku(sku, data)