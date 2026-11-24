from pwdlib import PasswordHash
from starlette.concurrency import run_in_threadpool

from app.core.exceptions.errors import ConflictError
from app.modules.auth.repositories import UserRepository
from app.modules.auth.schemas import UserRead, UserRegister
from app.core.exceptions.errors import ConflictError, UnauthorizedError
from app.core.security import create_access_token, read_access_token
from app.modules.auth.schemas import TokenRead, UserRead, UserRegister


password_hasher = PasswordHash.recommended()
dummy_password_hash = password_hasher.hash("pharmashelf-login-timing-check")




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

    

    async def login(self, email: str, password: str) -> TokenRead:

        user = await self.repository.get_by_email(email.strip().lower())

        stored_hash = user.password_hash if user else dummy_password_hash

        password_matches = await run_in_threadpool(
            password_hasher.verify, password, stored_hash
        )

        if user is None or not password_matches or not user.is_active:
            raise UnauthorizedError("Invalid email or password")

        return TokenRead(access_token=create_access_token(user.id))

    

    async def get_current_user(self, token: str) -> UserRead:
        
        user_id = read_access_token(token)
        user = await self.repository.get_by_id(user_id)

        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid or expired access token")

        return UserRead.model_validate(user)