import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SAEnum,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class SessionStatus(str, enum.Enum):
    pending = "pending"
    identifying = "identifying"
    identified = "identified"
    matching = "matching"
    complete = "complete"


class PhotoStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(SAEnum(SessionStatus), nullable=False, default=SessionStatus.pending)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    expires_at = Column(DateTime, nullable=False)


class SessionPhoto(Base):
    __tablename__ = "session_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    celery_task_id = Column(String(200), nullable=True)
    status = Column(SAEnum(PhotoStatus), nullable=False, default=PhotoStatus.pending)
    raw_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SessionBomEntry(Base):
    __tablename__ = "session_bom_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    part_num = Column(String(20), nullable=False)
    color_id = Column(Integer, nullable=True)  # null = color unknown
    quantity = Column(Integer, nullable=False, default=1)
    confidence = Column(Float, nullable=True)
    source = Column(String(50), nullable=False, default="manual")  # "photo" | "manual"
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    set_num = Column(String(20), nullable=False)
    match_mode = Column(String(20), nullable=False)  # "color_sensitive" | "color_agnostic"
    match_percentage = Column(Float, nullable=False)
    parts_matched = Column(Integer, nullable=False)
    parts_total = Column(Integer, nullable=False)
    missing_parts = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
