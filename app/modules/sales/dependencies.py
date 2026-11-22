from typing import Annotated

from fastapi import Depends

from app.db.session import SessionDep
from app.modules.sales.repositories import SaleRepository
from app.modules.sales.services import SaleService


def get_sale_service(session: SessionDep) -> SaleService:
    return SaleService(SaleRepository(session))


SaleServiceDep = Annotated[SaleService, Depends(get_sale_service)]