from typing import Annotated

from fastapi import Depends
from app.modules.inventory.services import StockReceiptService
from app.db.session import SessionDep
from app.modules.inventory.repositories import InventoryRepository
from app.modules.inventory.services import InventoryService


def get_inventory_service(session: SessionDep) -> InventoryService:
    repository = InventoryRepository(session)
    return InventoryService(repository)


InventoryServiceDep = Annotated[InventoryService, Depends(get_inventory_service)]


def get_stock_receipt_service(session: SessionDep) -> StockReceiptService:
    return StockReceiptService(InventoryRepository(session))


StockReceiptServiceDep = Annotated[
    StockReceiptService, Depends(get_stock_receipt_service)
]