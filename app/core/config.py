from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL
from pydantic import Field, SecretStr












class Settings(BaseSettings):


    APP_NAME: str = "PharmaShelf"
    DEBUG: bool = False

    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "pharmashelf"
    DB_USER: str = "pharmashelf"
    DB_PASSWORD: SecretStr
    JWT_SECRET: SecretStr = Field(min_length=32)
    ACCESS_TOKEN_MINUTES: int = Field(default=30, gt=0)
    GEMINI_API_KEY: SecretStr = Field(min_length=1)
    GEMINI_MODEL: str = Field(min_length=1)




    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )



    @property
    def DATABASE_URL(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.DB_USER,
            password=self.DB_PASSWORD.get_secret_value(),
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )




@lru_cache
def get_settings() -> Settings:
    return Settings()