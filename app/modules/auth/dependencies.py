from typing import Annotated

from fastapi import Depends

from app.db.session import SessionDep
from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthService
from fastapi.security import OAuth2PasswordBearer

from app.modules.auth.schemas import UserRead

from app.core.exceptions.errors import ForbiddenError


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(UserRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    service: AuthServiceDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserRead:
    return await service.get_current_user(token)


CurrentUserDep = Annotated[UserRead, Depends(get_current_user)]

def require_admin(user: CurrentUserDep) -> None:
    if user.role != "admin":
        raise ForbiddenError("Owner access required")

    
def require_inventory_staff(user: CurrentUserDep) -> None:
    if user.role not in {"admin", "staff"}:
        raise ForbiddenError("Owner or pharmacist access required")