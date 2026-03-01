import uuid as _uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.session import Session, SessionBomEntry
from app.schemas.bom import BomEntryCreate, BomEntryResponse, BomEntryUpdate

router = APIRouter(prefix="/sessions/{session_id}/bom", tags=["bom"])


async def get_session_or_404(session_id: UUID, db: AsyncSession) -> Session:
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("", response_model=list[BomEntryResponse])
async def get_bom(session_id: UUID, db: AsyncSession = Depends(get_db)):
    await get_session_or_404(session_id, db)
    result = await db.execute(
        select(SessionBomEntry).where(SessionBomEntry.session_id == session_id)
    )
    return result.scalars().all()


@router.post("", response_model=BomEntryResponse, status_code=201)
async def add_bom_entry(
    session_id: UUID,
    entry_in: BomEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    await get_session_or_404(session_id, db)
    entry = SessionBomEntry(
        id=_uuid.uuid4(),
        session_id=session_id,
        part_num=entry_in.part_num,
        color_id=entry_in.color_id,
        quantity=entry_in.quantity,
        source="manual",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.put("/{entry_id}", response_model=BomEntryResponse)
async def update_bom_entry(
    session_id: UUID,
    entry_id: UUID,
    update: BomEntryUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionBomEntry).where(
            SessionBomEntry.id == entry_id,
            SessionBomEntry.session_id == session_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="BOM entry not found")

    if update.quantity is not None:
        entry.quantity = update.quantity
    if update.color_id is not None:
        entry.color_id = update.color_id

    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
async def delete_bom_entry(
    session_id: UUID,
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionBomEntry).where(
            SessionBomEntry.id == entry_id,
            SessionBomEntry.session_id == session_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="BOM entry not found")
    await db.delete(entry)
    await db.commit()
