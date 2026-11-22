from pwdlib import PasswordHash
from starlette.concurrency import run_in_threadpool

from app.core.exceptions.errors import ConflictError
from app.modules.auth.repositories import UserRepository
from app.modules.auth.schemas import UserRead, UserRegister


password_hasher = PasswordHash.recommended()


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register(self, data: UserRegister) -> UserRead:
        email = str(data.email).lower()
        password_hash = await run_in_threadpool(
            password_hasher.hash,
            data.password.get_secret_value(),
        )

        user = await self.repository.create_customer(email, password_hash)
        if user is None:
            raise ConflictError("An account already exists for this email")

        return UserRead.model_validate(user)