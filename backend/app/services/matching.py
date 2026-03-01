from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID


async def run_matching(
    db: AsyncSession,
    session_id: UUID,
    mode: str,
) -> list[dict]:
    """
    Run set matching entirely in PostgreSQL using a LATERAL JOIN.
    Returns top 100 sets sorted by match percentage.
    mode: "color_sensitive" | "color_agnostic"
    """
    mv = "set_parts_mv" if mode == "color_sensitive" else "set_parts_agnostic_mv"

    if mode == "color_sensitive":
        join_condition = "sp.part_num = ub.part_num AND sp.color_id = ub.color_id"
        bom_select = """
            SELECT part_num, color_id, SUM(quantity) AS quantity
            FROM session_bom_entries
            WHERE session_id = :session_id AND color_id IS NOT NULL
            GROUP BY part_num, color_id
        """
    else:
        join_condition = "sp.part_num = ub.part_num"
        bom_select = """
            SELECT part_num, SUM(quantity) AS quantity
            FROM session_bom_entries
            WHERE session_id = :session_id
            GROUP BY part_num
        """

    sql = text(f"""
        WITH user_bom AS (
            {bom_select}
        )
        SELECT
            s.set_num,
            s.name AS set_name,
            s.year AS set_year,
            s.img_url AS set_img_url,
            s.num_parts,
            COALESCE(match.matched_qty, 0) AS parts_matched,
            CASE WHEN s.num_parts > 0
                 THEN ROUND(100.0 * COALESCE(match.matched_qty, 0) / s.num_parts, 1)
                 ELSE 0
            END AS match_percentage
        FROM sets s
        LEFT JOIN LATERAL (
            SELECT SUM(LEAST(sp.quantity, ub.quantity)) AS matched_qty
            FROM {mv} sp
            JOIN user_bom ub ON {join_condition}
            WHERE sp.set_num = s.set_num
        ) match ON true
        WHERE s.num_parts > 0
        ORDER BY match_percentage DESC, s.num_parts ASC
        LIMIT 100
    """)

    result = await db.execute(sql, {"session_id": str(session_id)})
    rows = result.mappings().all()
    return [dict(r) for r in rows]


async def get_missing_parts(
    db: AsyncSession,
    session_id: UUID,
    set_num: str,
    mode: str,
) -> list[dict]:
    """
    For a specific set, return list of pieces the user is missing or short on.
    """
    if mode == "color_sensitive":
        sql = text("""
            WITH user_bom AS (
                SELECT part_num, color_id, SUM(quantity) AS quantity
                FROM session_bom_entries
                WHERE session_id = :session_id AND color_id IS NOT NULL
                GROUP BY part_num, color_id
            )
            SELECT
                sp.part_num,
                sp.color_id,
                sp.quantity AS needed,
                COALESCE(ub.quantity, 0) AS have
            FROM set_parts_mv sp
            LEFT JOIN user_bom ub ON sp.part_num = ub.part_num AND sp.color_id = ub.color_id
            WHERE sp.set_num = :set_num
              AND sp.quantity > COALESCE(ub.quantity, 0)
            ORDER BY (sp.quantity - COALESCE(ub.quantity, 0)) DESC
        """)
    else:
        sql = text("""
            WITH user_bom AS (
                SELECT part_num, SUM(quantity) AS quantity
                FROM session_bom_entries
                WHERE session_id = :session_id
                GROUP BY part_num
            )
            SELECT
                sp.part_num,
                NULL::int AS color_id,
                sp.quantity AS needed,
                COALESCE(ub.quantity, 0) AS have
            FROM set_parts_agnostic_mv sp
            LEFT JOIN user_bom ub ON sp.part_num = ub.part_num
            WHERE sp.set_num = :set_num
              AND sp.quantity > COALESCE(ub.quantity, 0)
            ORDER BY (sp.quantity - COALESCE(ub.quantity, 0)) DESC
        """)

    result = await db.execute(sql, {"session_id": str(session_id), "set_num": set_num})
    rows = result.mappings().all()
    return [dict(r) for r in rows]
