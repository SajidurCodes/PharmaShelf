from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.modules.inventory.dependencies import InventoryServiceDep
from app.modules.inventory.schemas import AvailabilityRead


router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/availability", response_model=AvailabilityRead)
async def get_availability(
    service: InventoryServiceDep,
    sku: Annotated[str, Query(min_length=1, max_length=64)],
    branch_code: Annotated[str, Query(min_length=1, max_length=40)],
) -> AvailabilityRead:
    result = await service.get_availability(sku, branch_code)

    if result is None:
        raise HTTPException(status_code=404, detail="Unknown medicine or branch")

    return result