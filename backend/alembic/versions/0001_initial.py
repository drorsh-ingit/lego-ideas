"""Initial schema: Rebrickable tables, application tables, and materialized views.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # Rebrickable reference tables
    # -------------------------------------------------------------------------

    op.create_table(
        "themes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["themes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "colors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("rgb", sa.String(6), nullable=False),
        sa.Column("is_trans", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "part_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "parts",
        sa.Column("part_num", sa.String(20), nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("part_cat_id", sa.Integer(), nullable=True),
        sa.Column("part_material", sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(["part_cat_id"], ["part_categories.id"]),
        sa.PrimaryKeyConstraint("part_num"),
    )

    op.create_table(
        "part_relationships",
        sa.Column("rel_type", sa.String(1), nullable=False),
        sa.Column("child_part_num", sa.String(20), nullable=False),
        sa.Column("parent_part_num", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(["child_part_num"], ["parts.part_num"]),
        sa.ForeignKeyConstraint(["parent_part_num"], ["parts.part_num"]),
        sa.PrimaryKeyConstraint("child_part_num", "parent_part_num"),
    )

    op.create_table(
        "sets",
        sa.Column("set_num", sa.String(20), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("theme_id", sa.Integer(), nullable=True),
        sa.Column("num_parts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("img_url", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["theme_id"], ["themes.id"]),
        sa.PrimaryKeyConstraint("set_num"),
    )

    op.create_table(
        "inventories",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("set_num", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(["set_num"], ["sets.set_num"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "inventory_parts",
        sa.Column("inventory_id", sa.Integer(), nullable=False),
        sa.Column("part_num", sa.String(20), nullable=False),
        sa.Column("color_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_spare", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("img_url", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["color_id"], ["colors.id"]),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventories.id"]),
        sa.ForeignKeyConstraint(["part_num"], ["parts.part_num"]),
        sa.PrimaryKeyConstraint("inventory_id", "part_num", "color_id"),
    )

    # -------------------------------------------------------------------------
    # Application tables
    # -------------------------------------------------------------------------

    # Enums
    session_status_enum = sa.Enum(
        "pending", "identifying", "identified", "matching", "complete",
        name="sessionstatus",
    )
    photo_status_enum = sa.Enum(
        "pending", "processing", "done", "failed",
        name="photostatus",
    )

    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("status", session_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "session_photos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("celery_task_id", sa.String(200), nullable=True),
        sa.Column("status", photo_status_enum, nullable=False, server_default="pending"),
        sa.Column("raw_response", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_photos_session_id", "session_photos", ["session_id"])

    op.create_table(
        "session_bom_entries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("part_num", sa.String(20), nullable=False),
        sa.Column("color_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_session_bom_entries_session_id", "session_bom_entries", ["session_id"]
    )

    op.create_table(
        "match_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("set_num", sa.String(20), nullable=False),
        sa.Column("match_mode", sa.String(20), nullable=False),
        sa.Column("match_percentage", sa.Float(), nullable=False),
        sa.Column("parts_matched", sa.Integer(), nullable=False),
        sa.Column("parts_total", sa.Integer(), nullable=False),
        sa.Column("missing_parts", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_match_results_session_id_mode",
        "match_results",
        ["session_id", "match_mode"],
    )

    # -------------------------------------------------------------------------
    # Materialized views
    # -------------------------------------------------------------------------

    # Color-sensitive: group by set_num, part_num, color_id
    op.execute("""
        CREATE MATERIALIZED VIEW set_parts_mv AS
        SELECT
            i.set_num,
            ip.part_num,
            ip.color_id,
            SUM(ip.quantity) AS quantity
        FROM inventories i
        JOIN inventory_parts ip ON ip.inventory_id = i.id
        WHERE ip.is_spare = false
        GROUP BY i.set_num, ip.part_num, ip.color_id
        WITH NO DATA
    """)
    op.execute("CREATE INDEX idx_set_parts_mv_set_num ON set_parts_mv(set_num)")
    op.execute(
        "CREATE INDEX idx_set_parts_mv_lookup ON set_parts_mv(part_num, color_id)"
    )

    # Color-agnostic: group by set_num, part_num only
    op.execute("""
        CREATE MATERIALIZED VIEW set_parts_agnostic_mv AS
        SELECT
            i.set_num,
            ip.part_num,
            SUM(ip.quantity) AS quantity
        FROM inventories i
        JOIN inventory_parts ip ON ip.inventory_id = i.id
        WHERE ip.is_spare = false
        GROUP BY i.set_num, ip.part_num
        WITH NO DATA
    """)
    op.execute(
        "CREATE INDEX idx_set_parts_agnostic_mv_set_num ON set_parts_agnostic_mv(set_num)"
    )
    op.execute(
        "CREATE INDEX idx_set_parts_agnostic_mv_lookup ON set_parts_agnostic_mv(part_num)"
    )


def downgrade() -> None:
    # Drop materialized views first
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_parts_agnostic_mv")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS set_parts_mv")

    # Drop application tables
    op.drop_table("match_results")
    op.drop_table("session_bom_entries")
    op.drop_table("session_photos")
    op.drop_table("sessions")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS photostatus")
    op.execute("DROP TYPE IF EXISTS sessionstatus")

    # Drop Rebrickable tables (in reverse dependency order)
    op.drop_table("inventory_parts")
    op.drop_table("inventories")
    op.drop_table("sets")
    op.drop_table("part_relationships")
    op.drop_table("parts")
    op.drop_table("part_categories")
    op.drop_table("colors")
    op.drop_table("themes")
