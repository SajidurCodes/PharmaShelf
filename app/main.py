from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions.errors import ConflictError
from app.core.exceptions.handlers import handle_conflict

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
app.add_exception_handler(ConflictError, handle_conflict)
app.include_router(api_router)