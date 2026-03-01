import uuid as _uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.session import (
    PhotoStatus,
    Session,
    SessionBomEntry,
    SessionPhoto,
    SessionStatus,
)
from app.schemas.session import PhotoResponse
from app.services.storage import save_upload
from app.tasks.identify import identify_photo_task

router = APIRouter(prefix="/sessions/{session_id}/photos", tags=["photos"])


async def get_session_or_404(session_id: UUID, db: AsyncSession) -> Session:
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("", response_model=list[PhotoResponse], status_code=201)
async def upload_photos(
    session_id: UUID,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    session = await get_session_or_404(session_id, db)

    # Count existing photos
    result = await db.execute(
        select(SessionPhoto).where(SessionPhoto.session_id == session_id)
    )
    existing_count = len(result.scalars().all())

    if existing_count + len(files) > settings.max_photos_per_session:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.max_photos_per_session} photos per session",
        )

    photos = []
    for file in files:
        content = await file.read()

        if len(content) > settings.max_photo_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File {file.filename} too large")

        file_path = await save_upload(str(session_id), file.filename or "photo.jpg", content)

        photo = SessionPhoto(
            id=_uuid.uuid4(),
            session_id=session_id,
            filename=file.filename or "photo.jpg",
            file_path=str(file_path),
            status=PhotoStatus.pending,
        )
        db.add(photo)
        await db.flush()

        # Enqueue Celery task
        task = identify_photo_task.delay(str(photo.id), str(file_path))
        photo.celery_task_id = task.id

        photos.append(photo)

    session.status = SessionStatus.identifying
    await db.commit()

    for photo in photos:
        await db.refresh(photo)

    return photos


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    session_id: UUID,
    photo_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionPhoto).where(
            SessionPhoto.id == photo_id,
            SessionPhoto.session_id == session_id,
        )
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.post("/confirm", status_code=200)
async def confirm_photos(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Merge identified pieces from all done photos into BOM entries.
    """
    session = await get_session_or_404(session_id, db)

    result = await db.execute(
        select(SessionPhoto).where(
            SessionPhoto.session_id == session_id,
            SessionPhoto.status == PhotoStatus.done,
        )
    )
    photos = result.scalars().all()

    for photo in photos:
        if not photo.raw_response:
            continue
        items = photo.raw_response.get("items", [])
        for item in items:
            part_num = item.get("id")
            confidence = item.get("score", 0.0)
            if not part_num:
                continue
            entry = SessionBomEntry(
                id=_uuid.uuid4(),
                session_id=session_id,
                part_num=part_num,
                color_id=None,
                quantity=1,
                confidence=confidence,
                source="photo",
            )
            db.add(entry)

    session.status = SessionStatus.identified
    await db.commit()
    return {"status": "ok", "session_id": str(session_id)}
