from app.core.database import get_db  # noqa: F401
from app.core.config import settings, Settings


def get_settings() -> Settings:
    return settings
