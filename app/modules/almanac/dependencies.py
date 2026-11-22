from typing import Annotated

from fastapi import Depends

from app.db.session import SessionDep
from app.modules.almanac.repositories import AlmanacRepository
from app.modules.almanac.services import AlmanacService


def get_almanac_service(session: SessionDep) -> AlmanacService:
    return AlmanacService(AlmanacRepository(session))


AlmanacServiceDep = Annotated[AlmanacService, Depends(get_almanac_service)]
