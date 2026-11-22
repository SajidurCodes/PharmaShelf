from fastapi import APIRouter, Depends, Response, status

from app.modules.auth.dependencies import require_admin
from app.modules.sales.dependencies import SaleServiceDep
from app.modules.sales.schemas import SaleCreate, SaleRead


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