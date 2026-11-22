from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.core.exceptions.handlers import handle_conflict, handle_forbidden, handle_not_found, handle_unauthorized


settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
app.add_exception_handler(ConflictError, handle_conflict)
app.add_exception_handler(ForbiddenError, handle_forbidden)
app.add_exception_handler(NotFoundError, handle_not_found)
app.include_router(api_router)
app.add_exception_handler(UnauthorizedError, handle_unauthorized)
