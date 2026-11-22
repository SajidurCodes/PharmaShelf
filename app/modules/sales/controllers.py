from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.db.session import SessionDep
from app.modules.auth.dependencies import require_admin, require_inventory_staff
from app.modules.sales.dependencies import SaleServiceDep
from app.modules.sales.schemas import (
    BestSellerFilters,
    BestSellerRead,
    SaleCreate,
    SaleRead,
)
from app.modules.sales.spikes import SpikeReport, get_demand_spikes
from app.modules.sales.trends import DemandTrend, get_demand_trend


router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post(
    "",
    response_model=SaleRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {
            "model": SaleRead,
            "description": "Previously recorded sale",
        }
    },
    dependencies=[Depends(require_inventory_staff)],
)
async def record_sale(
    data: SaleCreate,
    response: Response,
    service: SaleServiceDep,
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


@router.get(
    "/demand-trend",
    response_model=DemandTrend,
    dependencies=[Depends(require_admin)],
)
async def demand_trend(
    session: SessionDep,
    branch_code: Annotated[str, Query(min_length=1, max_length=40)],
    sku: Annotated[str, Query(min_length=1, max_length=64)],
    start_date: date,
    end_date: date,
) -> DemandTrend:
    try:
        return await get_demand_trend(
            session=session,
            branch_code=branch_code.strip(),
            sku=sku.strip(),
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/demand-spikes",
    response_model=SpikeReport,
    dependencies=[Depends(require_admin)],
)
async def demand_spikes(
    session: SessionDep,
    branch_code: Annotated[str, Query(min_length=1, max_length=40)],
) -> SpikeReport:
    return await get_demand_spikes(session, branch_code.strip())