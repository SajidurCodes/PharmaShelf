from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.errors import ConflictError, UnauthorizedError


async def handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})

async def handle_unauthorized(request: Request, exc: UnauthorizedError) -> JSONResponse:
    
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )