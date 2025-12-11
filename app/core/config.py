"""Application configuration for OpenMusic API.

Defines a Settings class backed by pydantic-settings to load environment
variables from a .env file (case-sensitive). Exposes a computed async
SQLAlchemy DSN for database connectivity using the asyncpg driver.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field
from typing import Optional

class Settings(BaseSettings):
    """Application configuration backed by environment variables.

    Loads settings from the project's .env file (case-sensitive) and exposes
    derived configuration such as the async SQLAlchemy DSN for database access.

    Attributes:
        POSTGRES_USER: Database user.
        POSTGRES_PASSWORD: Database password.
        POSTGRES_SERVER: Database hostname or IP.
        POSTGRES_PORT: Database port number.
        POSTGRES_DB: Database name.

    Properties:
        SQLALCHEMY_DATABASE_URI: Async SQLAlchemy DSN using the asyncpg driver.
    """
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    ACCESS_TOKEN_KEY: str
    REFRESH_TOKEN_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int

    # RabbitMQ
    RABBITMQ_SERVER: str
    RABBITMQ_USERNAME: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_ERLANG_COOKIE: str

    # SMTP
    SMTP_HOST: Optional[str]
    SMTP_PORT: Optional[int]
    SMTP_USER: Optional[str]
    SMTP_PASSWORD: Optional[str]
    MAIL_FROM: str

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET_NAME: str

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Build the async SQLAlchemy database URI.

        Constructs a PostgreSQL DSN using the asyncpg driver from the
        configured POSTGRES_* fields.

        Returns:
            The DSN string (e.g. 'postgresql+asyncpg://user:pass@host:port/db').
        """
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        ))

settings = Settings()
