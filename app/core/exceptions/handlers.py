from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError



async def handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:

    return JSONResponse(status_code=409, content={"detail": str(exc)})



async def handle_unauthorized(request: Request, exc: UnauthorizedError) -> JSONResponse:
    
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def handle_forbidden(request: Request, exc: ForbiddenError) -> JSONResponse:

    return JSONResponse(status_code=403, content={"detail": str(exc)})

async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    
    return JSONResponse(status_code=404, content={"detail": str(exc)})