import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import password_hasher


# Public credentials for the local Docker demo, also listed in the README.
DEMO_USERS = (
    ("owner@pharmashelf.example.com", "admin", "Demo-Owner-7Qm4-2026!"),
    ("staff@pharmashelf.example.com", "staff", "Demo-Staff-9Kp2-2026!"),
    ("customer@pharmashelf.example.com", "customer", "Demo-Customer-3Vr8-2026!"),
)


async def main() -> None:
    created = 0

    async with SessionLocal.begin() as session:
        repository = UserRepository(session)

        for email, role, password in DEMO_USERS:
            user = await repository.get_by_email(email)

            if user is None:
                statement = (
                    insert(User)
                    .values(
                        email=email,
                        role=role,
                        password_hash=password_hasher.hash(password),
                        is_active=True,
                    )
                    .on_conflict_do_nothing(index_elements=[User.email])
                    .returning(User.id)
                )
                if await session.scalar(statement) is not None:
                    created += 1
                    continue

                # Another seed process may have inserted the same email.
                user = await repository.get_by_email(email)

            if (
                user is None
                or user.role != role
                or not user.is_active
                or not password_hasher.verify(password, user.password_hash)
            ):
                raise RuntimeError(
                    f"Demo account conflict for {email}. "
                    "Check the existing account before using this demo email."
                )

    print(f"Demo accounts ready: {len(DEMO_USERS)}. Newly created: {created}.")


if __name__ == "__main__":
    asyncio.run(main())