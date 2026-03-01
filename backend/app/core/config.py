from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://lego:legopass@localhost:5432/legoideas"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    upload_dir: str = "./uploads"
    brickognize_api_url: str = "https://api.brickognize.com"
    session_ttl_hours: int = 24
    max_photos_per_session: int = 5
    max_photo_size_mb: int = 20
    # Comma-separated list of allowed CORS origins. Use "*" for local dev only.
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
