from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class MissingPart(BaseModel):
    part_num: str
    color_id: int | None
    needed: int
    have: int


class MatchResultResponse(BaseModel):
    session_id: UUID
    set_num: str
    set_name: str
    set_year: int | None
    set_img_url: str | None
    match_mode: str
    match_percentage: float
    parts_matched: int
    parts_total: int
    missing_parts: list[MissingPart] | None = None


class MatchRequest(BaseModel):
    mode: str = "color_sensitive"  # "color_sensitive" | "color_agnostic"
