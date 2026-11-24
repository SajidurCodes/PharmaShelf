from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.core.config import get_settings
from app.core.exceptions.errors import UnauthorizedError




def create_access_token(user_id: UUID) -> str:

    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_MINUTES
    )


    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        settings.JWT_SECRET.get_secret_value(),
        algorithm="HS256",
    )




def read_access_token(token: str) -> UUID:


    try:
        claims = jwt.decode(
            token,
            get_settings().JWT_SECRET.get_secret_value(),
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        return UUID(claims["sub"])

    
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise UnauthorizedError("Invalid or expired access token") from None