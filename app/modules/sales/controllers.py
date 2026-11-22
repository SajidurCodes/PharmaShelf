from fastapi import APIRouter, Depends, Response, status

from app.modules.auth.dependencies import require_admin
from app.modules.sales.dependencies import SaleServiceDep


from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.sales.schemas import (
    BestSellerFilters,
    BestSellerRead,
    SaleCreate,
    SaleRead,
)


router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post(
    "",
    response_model=SaleRead,
    status_code=status.HTTP_201_CREATED,
    responses={200: {"model": SaleRead, "description": "Previously recorded sale"}},
    dependencies=[Depends(require_admin)],
)
async def record_sale(
    data: SaleCreate, response: Response, service: SaleServiceDep
) -> SaleRead:
    sale, created = await service.record(data)
    if not created:
        response.status_code = status.HTTP_200_OK
    return sale



@router.get(
    "/best-sellers",
    response_model=list[BestSellerRead],
    dependencies=[Depends(require_admin)],
)
async def best_sellers(
    filters: Annotated[BestSellerFilters, Query()],
    service: SaleServiceDep,
) -> list[BestSellerRead]:
    return await service.best_sellers(filters)