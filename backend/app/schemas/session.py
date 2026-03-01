from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.models.session import SessionStatus, PhotoStatus


class SessionCreate(BaseModel):
    pass


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: SessionStatus
    created_at: datetime
    expires_at: datetime


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    filename: str
    status: PhotoStatus
    raw_response: dict | None = None
    created_at: datetime
