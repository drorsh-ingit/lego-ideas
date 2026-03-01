import uuid as _uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.session import MatchResult, Session, SessionStatus
from app.schemas.results import MatchRequest, MatchResultResponse, MissingPart
from app.services.matching import get_missing_parts, run_matching

router = APIRouter(prefix="/sessions/{session_id}", tags=["matching"])


async def get_session_or_404(session_id: UUID, db: AsyncSession) -> Session:
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/match", status_code=202)
async def run_match(
    session_id: UUID,
    req: MatchRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await get_session_or_404(session_id, db)

    session.status = SessionStatus.matching
    await db.commit()

    rows = await run_matching(db, session_id, req.mode)

    # Delete old results for this session+mode
    await db.execute(
        delete(MatchResult).where(
            MatchResult.session_id == session_id,
            MatchResult.match_mode == req.mode,
        )
    )

    for row in rows:
        mr = MatchResult(
            id=_uuid.uuid4(),
            session_id=session_id,
            set_num=row["set_num"],
            match_mode=req.mode,
            match_percentage=float(row["match_percentage"] or 0),
            parts_matched=int(row["parts_matched"] or 0),
            parts_total=int(row["num_parts"] or 0),
        )
        db.add(mr)

    session.status = SessionStatus.complete
    await db.commit()

    return {"status": "complete", "results_count": len(rows)}


@router.get("/results", response_model=list[MatchResultResponse])
async def get_results(
    session_id: UUID,
    mode: str = "color_sensitive",
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    await get_session_or_404(session_id, db)

    sql = text("""
        SELECT mr.*, s.name AS set_name, s.year AS set_year, s.img_url AS set_img_url
        FROM match_results mr
        JOIN sets s ON s.set_num = mr.set_num
        WHERE mr.session_id = :session_id AND mr.match_mode = :mode
        ORDER BY mr.match_percentage DESC
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(
        sql,
        {
            "session_id": str(session_id),
            "mode": mode,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        },
    )
    rows = result.mappings().all()

    return [
        MatchResultResponse(
            session_id=session_id,
            set_num=r["set_num"],
            set_name=r["set_name"],
            set_year=r["set_year"],
            set_img_url=r["set_img_url"],
            match_mode=r["match_mode"],
            match_percentage=float(r["match_percentage"]),
            parts_matched=int(r["parts_matched"]),
            parts_total=int(r["parts_total"]),
        )
        for r in rows
    ]


@router.get("/results/{set_num}", response_model=MatchResultResponse)
async def get_result_detail(
    session_id: UUID,
    set_num: str,
    mode: str = "color_sensitive",
    db: AsyncSession = Depends(get_db),
):
    sql = text("""
        SELECT mr.*, s.name AS set_name, s.year AS set_year, s.img_url AS set_img_url
        FROM match_results mr
        JOIN sets s ON s.set_num = mr.set_num
        WHERE mr.session_id = :session_id AND mr.set_num = :set_num AND mr.match_mode = :mode
    """)
    result = await db.execute(
        sql,
        {
            "session_id": str(session_id),
            "set_num": set_num,
            "mode": mode,
        },
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")

    missing = await get_missing_parts(db, session_id, set_num, mode)

    return MatchResultResponse(
        session_id=session_id,
        set_num=row["set_num"],
        set_name=row["set_name"],
        set_year=row["set_year"],
        set_img_url=row["set_img_url"],
        match_mode=row["match_mode"],
        match_percentage=float(row["match_percentage"]),
        parts_matched=int(row["parts_matched"]),
        parts_total=int(row["parts_total"]),
        missing_parts=[
            MissingPart(
                part_num=m["part_num"],
                color_id=m["color_id"],
                needed=m["needed"],
                have=m["have"],
            )
            for m in missing
        ],
    )
