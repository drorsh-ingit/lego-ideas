import uuid
from pathlib import Path

from app.core.config import settings


def get_upload_path(session_id: str, filename: str) -> Path:
    ext = Path(filename).suffix or ".jpg"
    unique_name = f"{uuid.uuid4()}{ext}"
    upload_dir = Path(settings.upload_dir) / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / unique_name


async def save_upload(session_id: str, filename: str, data: bytes) -> Path:
    path = get_upload_path(session_id, filename)
    path.write_bytes(data)
    return path
