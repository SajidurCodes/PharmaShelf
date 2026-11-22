from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.db.session import SessionDep
from app.modules.auth.dependencies import require_admin, require_inventory_staff
from app.modules.inventory.dependencies import InventoryServiceDep, StockReceiptServiceDep
from app.modules.inventory.reorder import ReorderReport, get_reorder_report
from app.modules.inventory.schemas import (
    AvailabilityRead,
    ExpiryRescueReport,
    StockReceiptCreate,
    StockReceiptRead,
)


router = APIRouter(prefix="/inventory", tags=["Inventory"])

BranchCode = Annotated[str, Query(min_length=1, max_length=40)]


@router.get("/availability", response_model=AvailabilityRead)
async def get_availability(
    service: InventoryServiceDep,
    sku: Annotated[str, Query(min_length=1, max_length=64)],
    branch_code: BranchCode,
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
    branch_code: BranchCode,
    days: Annotated[int, Query(ge=1, le=60)] = 30,
) -> ExpiryRescueReport:
    return await service.expiry_rescue(branch_code.strip(), days)


@router.post(
    "/receipts",
    response_model=StockReceiptRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {
            "model": StockReceiptRead,
            "description": "Previously recorded delivery",
        }
    },
    dependencies=[Depends(require_inventory_staff)],
)
async def record_stock_receipt(
    data: StockReceiptCreate,
    response: Response,
    service: StockReceiptServiceDep,
) -> StockReceiptRead:
    receipt, created = await service.record(data)
    if not created:
        response.status_code = status.HTTP_200_OK

    return receipt


@router.get(
    "/reorder",
    response_model=ReorderReport,
    dependencies=[Depends(require_admin)],
)
async def reorder_report(
    session: SessionDep,
    branch_code: BranchCode,
) -> ReorderReport:
    return await get_reorder_report(session, branch_code.strip())