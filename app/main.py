from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
app.include_router(api_router)