from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.medicines.controllers import router as medicines_router
from app.modules.inventory.controllers import router as inventory_router
from app.modules.auth.controllers import router as auth_router
from app.modules.chat.controllers import router as chat_router
from app.modules.sales.controllers import router as sales_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(medicines_router)
api_router.include_router(inventory_router)
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(sales_router)