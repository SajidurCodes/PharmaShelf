from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.errors import ConflictError


async def handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})