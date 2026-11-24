from app.core.exceptions.errors import ConflictError, NotFoundError
from app.modules.almanac.repositories import AlmanacRepository
from app.modules.almanac.schemas import (
    AlmanacEntryCreate,
    AlmanacEntryRead,
    AlmanacEntryUpdate,
)




class AlmanacService:

    def __init__(self, repository: AlmanacRepository):

        self.repository = repository

    async def create(self, data: AlmanacEntryCreate) -> AlmanacEntryRead:

        session = self.repository.session

        try:

            entry = await self.repository.create(data)
            if entry is None:
                raise ConflictError(f"An Almanac entry with slug '{data.slug}' already exists")

            result = AlmanacEntryRead.model_validate(entry)
            await session.commit()
            return result

        
        except Exception:
            await session.rollback()
            raise

    async def get_by_slug(self,slug: str,*,active_only: bool = False,) -> AlmanacEntryRead:

        entry = await self.repository.get_by_slug(slug, active_only=active_only)
        if entry is None:
            raise NotFoundError(f"Almanac entry '{slug}' was not found")

        return AlmanacEntryRead.model_validate(entry)

    async def list_entries(self,*,topic: str | None = None,limit: int = 50,offset: int = 0,) -> list[AlmanacEntryRead]:

        entries = await self.repository.list_entries(
            topic=topic,
            limit=limit,
            offset=offset,
        )

        return [AlmanacEntryRead.model_validate(entry) for entry in entries]



    async def list_active(self,*,topic: str | None = None,limit: int = 50,offset: int = 0,) -> list[AlmanacEntryRead]:

        entries = await self.repository.list_active(
            topic=topic,
            limit=limit,
            offset=offset,
        )


        return [AlmanacEntryRead.model_validate(entry) for entry in entries]



    async def update_by_slug(self,slug: str,data: AlmanacEntryUpdate,) -> AlmanacEntryRead:
        
        
        session = self.repository.session

        try:
            entry = await self.repository.update_by_slug(slug, data)
            if entry is None:
                raise NotFoundError(f"Almanac entry '{slug}' was not found")

            result = AlmanacEntryRead.model_validate(entry)
            await session.commit()
            return result


        
        except Exception:
            await session.rollback()
            raise