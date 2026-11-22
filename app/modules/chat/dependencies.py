from typing import Annotated

from fastapi import Depends

from app.modules.chat.tools import CustomerCatalogTools
from app.modules.inventory.dependencies import InventoryServiceDep
from app.modules.medicines.dependencies import MedicineServiceDep


def get_customer_catalog_tools(
    medicine_service: MedicineServiceDep,
    inventory_service: InventoryServiceDep,
) -> CustomerCatalogTools:
    return CustomerCatalogTools(medicine_service, inventory_service)


CustomerCatalogToolsDep = Annotated[
    CustomerCatalogTools, Depends(get_customer_catalog_tools)
]