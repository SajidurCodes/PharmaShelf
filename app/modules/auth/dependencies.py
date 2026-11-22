from typing import Annotated

from fastapi import Depends

from app.db.session import SessionDep
from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthService


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(UserRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]