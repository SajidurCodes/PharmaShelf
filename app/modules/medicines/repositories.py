from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.medicines.models import Medicine
from sqlalchemy.dialects.postgresql import insert

from app.modules.medicines.schemas import MedicineCreate


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

    async def create(self, data: MedicineCreate) -> Medicine | None:
        statement = (
            insert(Medicine)
            .values(**data.model_dump())
            .on_conflict_do_nothing(index_elements=[Medicine.sku])
            .returning(Medicine)
        )

        medicine = await self.session.scalar(statement)
        await self.session.commit()
        return medicine

    async def get_by_sku(self, sku: str) -> Medicine | None:
        statement = select(Medicine).where(Medicine.sku == sku)
        return await self.session.scalar(statement)