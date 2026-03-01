from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class BomEntryCreate(BaseModel):
    part_num: str
    color_id: int | None = None
    quantity: int = 1


class BomEntryUpdate(BaseModel):
    quantity: int | None = None
    color_id: int | None = None


class BomEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    part_num: str
    color_id: int | None
    quantity: int
    confidence: float | None
    source: str
    created_at: datetime
