from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.db.session import SessionDep
from app.modules.almanac.dependencies import AlmanacServiceDep
from app.modules.almanac.schemas import (
    AlmanacEntryCreate,
    AlmanacEntryRead,
    AlmanacEntryUpdate,
    EntrySlug,
)
from app.modules.almanac.search import AlmanacSearchHit, search_almanac
from app.modules.auth.dependencies import require_admin


router = APIRouter(
    prefix="/almanac",
    tags=["Almanac"],
    dependencies=[Depends(require_admin)],
)


@router.post(
    "",
    response_model=AlmanacEntryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_entry(
    data: AlmanacEntryCreate,
    service: AlmanacServiceDep,
) -> AlmanacEntryRead:
    return await service.create(data)


@router.get("", response_model=list[AlmanacEntryRead])
async def list_entries(
    service: AlmanacServiceDep,
    topic: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AlmanacEntryRead]:
    return await service.list_entries(
        topic=topic.strip() if topic is not None else None,
        limit=limit,
        offset=offset,
    )


@router.get("/search", response_model=list[AlmanacSearchHit])
async def search_entries(
    session: SessionDep,
    q: Annotated[str, Query(min_length=1, max_length=500)],
    limit: Annotated[int, Query(ge=1, le=10)] = 3,
) -> list[AlmanacSearchHit]:
    return await search_almanac(session, q, limit=limit)


@router.get("/{slug}", response_model=AlmanacEntryRead)
async def get_entry(
    slug: EntrySlug,
    service: AlmanacServiceDep,
) -> AlmanacEntryRead:
    return await service.get_by_slug(slug)


@router.patch("/{slug}", response_model=AlmanacEntryRead)
async def update_entry(
    slug: EntrySlug,
    data: AlmanacEntryUpdate,
    service: AlmanacServiceDep,
) -> AlmanacEntryRead:
    return await service.update_by_slug(slug, data)