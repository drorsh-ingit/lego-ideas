from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.rebrickable import Color, InventoryPart, Part

router = APIRouter(tags=["reference"])


@router.get("/parts")
async def search_parts(
    search: str = Query("", min_length=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Part.part_num, Part.name)
    if search:
        stmt = stmt.where(
            Part.name.ilike(f"%{search}%") | Part.part_num.ilike(f"%{search}%")
        )
    stmt = stmt.limit(20)
    result = await db.execute(stmt)
    return [{"part_num": r.part_num, "name": r.name} for r in result]


@router.get("/parts/{part_num}")
async def get_part(part_num: str, db: AsyncSession = Depends(get_db)):
    part_result = await db.execute(
        select(Part.part_num, Part.name).where(Part.part_num == part_num)
    )
    part = part_result.one_or_none()

    # Get any available image URL from inventory_parts
    img_result = await db.execute(
        select(InventoryPart.img_url)
        .where(InventoryPart.part_num == part_num, InventoryPart.img_url.isnot(None))
        .limit(1)
    )
    img_row = img_result.one_or_none()

    return {
        "part_num": part_num,
        "name": part.name if part else part_num,
        "img_url": img_row.img_url if img_row else None,
    }


@router.get("/colors")
async def list_colors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Color).order_by(Color.name))
    colors = result.scalars().all()
    return [
        {"id": c.id, "name": c.name, "rgb": c.rgb, "is_trans": c.is_trans}
        for c in colors
    ]
