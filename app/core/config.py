"""Application configuration for OpenMusic API.

Defines a Settings class backed by pydantic-settings to load environment
variables from a .env file (case-sensitive). Exposes a computed async
SQLAlchemy DSN for database connectivity using the asyncpg driver.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field, field_validator
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

    SECRET_KEY: str
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

    LOG_LEVEL: str = "INFO"

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

    @computed_field
    @property
    def REDIS_SERVER(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @field_validator("SECRET_KEY", "ACCESS_TOKEN_KEY", "REFRESH_TOKEN_KEY")
    @classmethod
    def _not_empty(cls, value: str, info):
        if value is None or not str(value).strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return value

    @field_validator("RABBITMQ_ERLANG_COOKIE")
    @classmethod
    def _validate_erlang_cookie(cls, value: str):
        if value is None or len(value) < 32:
            raise ValueError("RABBITMQ_ERLANG_COOKIE must be at least 32 characters")
        return value

    @field_validator("POSTGRES_PASSWORD")
    @classmethod
    def _validate_postgres_password(cls, value: str):
        if value is None or not str(value).strip():
            raise ValueError("POSTGRES_PASSWORD must not be empty")
        if str(value).lower() == "password":
            raise ValueError("POSTGRES_PASSWORD must not be 'password'")
        return value

    @field_validator("LOG_LEVEL")
    @classmethod
    def _normalize_log_level(cls, value: str):
        lvl = str(value).upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if lvl not in allowed:
            raise ValueError("LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL")
        return lvl

    @field_validator("RABBITMQ_SERVER")
    @classmethod
    def _validate_rabbitmq_server(cls, value: str):
        if not value or not value.startswith("amqp"):
            raise ValueError("RABBITMQ_SERVER must be a valid amqp URL")
        return value

    @field_validator("MINIO_ENDPOINT")
    @classmethod
    def _validate_minio_endpoint(cls, value: str):
        if ":" not in value:
            raise ValueError("MINIO_ENDPOINT must include host and port")
        return value

    @field_validator("REDIS_HOST")
    @classmethod
    def _validate_redis_host(cls, value: str):
        if not value or not str(value).strip():
            raise ValueError("REDIS_HOST must not be empty")
        return value

settings = Settings()
