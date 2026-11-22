from fastapi import APIRouter, status

from app.modules.auth.dependencies import AuthServiceDep
from app.modules.auth.schemas import UserRead, UserRegister


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, service: AuthServiceDep) -> UserRead:
    return await service.register(data)