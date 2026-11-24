from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionDep


router = APIRouter(tags=["Health"])



@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
async def database_health(session: SessionDep) -> dict[str, str]:

    try:


        result = await session.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        )


        vector_version = result.scalar_one_or_none()

    except (SQLAlchemyError, OSError):


        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from None
    

    if vector_version is None:
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The vector extension is missing",
        )

    return {"database": "connected", "pgvector": vector_version}