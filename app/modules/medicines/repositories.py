from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.medicines.models import Medicine


class MedicineRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, query: str, limit: int) -> list[Medicine]:
        statement = select(Medicine)

        if query:
            statement = statement.where(
                or_(
                    Medicine.sku.icontains(query, autoescape=True),
                    Medicine.name.icontains(query, autoescape=True),
                    Medicine.generic_name.icontains(query, autoescape=True),
                )
            )

        statement = statement.order_by(Medicine.name, Medicine.sku).limit(limit)
        result = await self.session.scalars(statement)
        return list(result)