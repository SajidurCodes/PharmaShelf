from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.modules.auth.dependencies import require_admin
from app.modules.inventory.dependencies import InventoryServiceDep
from app.modules.inventory.schemas import AvailabilityRead, ExpiryRescueReport


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


@router.get(
    "/expiry-rescue",
    response_model=ExpiryRescueReport,
    dependencies=[Depends(require_admin)],
)
async def expiry_rescue(
    service: InventoryServiceDep,
    branch_code: Annotated[str, Query(min_length=1, max_length=40)],
    days: Annotated[int, Query(ge=1, le=60)] = 30,
) -> ExpiryRescueReport:
    return await service.expiry_rescue(branch_code.strip(), days)