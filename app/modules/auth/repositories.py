from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_customer(self, email: str, password_hash: str) -> User | None:
        statement = (
            insert(User)
            .values(email=email, password_hash=password_hash)
            .on_conflict_do_nothing(index_elements=[User.email])
            .returning(User)
        )

        async with self.session.begin():
            return await self.session.scalar(statement)