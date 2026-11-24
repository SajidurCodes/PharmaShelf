from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.almanac.models import AlmanacEntry
from app.modules.almanac.schemas import AlmanacEntryCreate, AlmanacEntryUpdate




class AlmanacRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: AlmanacEntryCreate) -> AlmanacEntry | None:
        
        statement = (
            insert(AlmanacEntry)
            .values(**data.model_dump())
            .on_conflict_do_nothing(index_elements=[AlmanacEntry.slug])
            .returning(AlmanacEntry)
        )
        return await self.session.scalar(statement)

    

    async def get_by_slug(self,slug: str,*,active_only: bool = False,) -> AlmanacEntry | None:

        statement = select(AlmanacEntry).where(AlmanacEntry.slug == slug)

        if active_only:
            statement = statement.where(AlmanacEntry.is_active.is_(True))

        return await self.session.scalar(statement)

    async def list_entries(self,*,topic: str | None = None,active_only: bool = False,limit: int = 50,offset: int = 0,) -> list[AlmanacEntry]:


        statement = select(AlmanacEntry)

        if topic is not None:
            statement = statement.where(AlmanacEntry.topic == topic)

        if active_only:
            statement = statement.where(AlmanacEntry.is_active.is_(True))

        statement = (
            statement
            .order_by(AlmanacEntry.topic, AlmanacEntry.title, AlmanacEntry.slug)
            .limit(limit)
            .offset(offset)
        )

        entries = await self.session.scalars(statement)
        return list(entries)

    async def list_active(self,*,topic: str | None = None,limit: int = 50,offset: int = 0,) -> list[AlmanacEntry]:


        return await self.list_entries(
            topic=topic,
            active_only=True,
            limit=limit,
            offset=offset,
        )
    

    async def update_by_slug(self,slug: str,data: AlmanacEntryUpdate,) -> AlmanacEntry | None:
        
        changes = data.model_dump(exclude_unset=True)

        statement = (
            update(AlmanacEntry)
            .where(AlmanacEntry.slug == slug)
            .values(**changes)
            .returning(AlmanacEntry)
            .execution_options(populate_existing=True)
        )
        return await self.session.scalar(statement)