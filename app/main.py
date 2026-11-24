from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.exceptions.handlers import (
    handle_conflict,
    handle_forbidden,
    handle_not_found,
    handle_unauthorized,
)
from app.mcp_server import mcp




settings = get_settings()
frontend_dir = Path(__file__).resolve().parent / "frontend"

mcp_http_app = mcp.streamable_http_app()



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield



app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)



app.add_exception_handler(ConflictError, handle_conflict)
app.add_exception_handler(ForbiddenError, handle_forbidden)
app.add_exception_handler(NotFoundError, handle_not_found)
app.add_exception_handler(UnauthorizedError, handle_unauthorized)

app.include_router(api_router)
app.mount("/studio", StaticFiles(directory=frontend_dir, html=True), name="studio")


app.mount("/", mcp_http_app, name="mcp")