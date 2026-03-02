#!/usr/bin/env python3
"""
Download Rebrickable CSV dumps and import them into PostgreSQL.
Usage: DATABASE_URL="postgresql://..." python scripts/import_rebrickable.py
"""
import gzip
import io
import os
import sys

import httpx
import psycopg2

DB_URL = os.environ.get("DATABASE_URL", "postgresql://lego:legopass@localhost:5432/legoideas")
DB_URL = DB_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

DOWNLOADS = [
    ("themes", "https://cdn.rebrickable.com/media/downloads/themes.csv.gz"),
    ("colors", "https://cdn.rebrickable.com/media/downloads/colors.csv.gz"),
    ("part_categories", "https://cdn.rebrickable.com/media/downloads/part_categories.csv.gz"),
    ("parts", "https://cdn.rebrickable.com/media/downloads/parts.csv.gz"),
    ("part_relationships", "https://cdn.rebrickable.com/media/downloads/part_relationships.csv.gz"),
    ("sets", "https://cdn.rebrickable.com/media/downloads/sets.csv.gz"),
    ("inventories", "https://cdn.rebrickable.com/media/downloads/inventories.csv.gz"),
    ("inventory_parts", "https://cdn.rebrickable.com/media/downloads/inventory_parts.csv.gz"),
]


def download_csv(url: str) -> bytes:
    print(f"  Downloading {url} ...")
    with httpx.Client(follow_redirects=True, timeout=120) as client:
        r = client.get(url)
        r.raise_for_status()
    if url.endswith(".gz"):
        return gzip.decompress(r.content)
    return r.content


def get_table_columns(cur, table_name: str) -> list[str]:
    """Return column names that actually exist in the table."""
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table_name,),
    )
    return [row[0] for row in cur.fetchall()]


def get_fk_filters(cur, table_name: str) -> list[tuple[str, str, str, bool]]:
    """Return (local_col, foreign_table, foreign_col, is_nullable) for each FK on the
    table, excluding self-referential FKs (which would filter everything on a fresh import)."""
    cur.execute(
        """
        SELECT kcu.column_name, ccu.table_name, ccu.column_name,
               col.is_nullable = 'YES'
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        JOIN information_schema.columns col
            ON col.table_schema = tc.table_schema
            AND col.table_name = tc.table_name
            AND col.column_name = kcu.column_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND tc.table_name = %s
        """,
        (table_name,),
    )
    return [
        row for row in cur.fetchall()
        if row[1] != table_name  # skip self-referential FKs
    ]


def import_table(conn, table_name: str, csv_bytes: bytes):
    import csv as csv_mod

    cur = conn.cursor()

    cur.execute(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE')
    conn.commit()

    # Parse CSV properly (handles quoted commas)
    text = csv_bytes.decode("utf-8")
    reader = csv_mod.DictReader(io.StringIO(text))
    csv_columns = reader.fieldnames or []

    # Only import columns that exist in our schema (e.g. skip colors.num_parts)
    db_columns = get_table_columns(cur, table_name)
    valid_columns = [c for c in csv_columns if c in db_columns]
    col_list = ", ".join(f'"{c}"' for c in valid_columns)

    # Build filtered CSV with only valid columns and copy via temp table
    tmp = f"_tmp_{table_name}"
    cur.execute(f'CREATE TEMP TABLE "{tmp}" AS SELECT {col_list} FROM "{table_name}" LIMIT 0')

    filtered = io.StringIO()
    writer = csv_mod.DictWriter(filtered, fieldnames=valid_columns, extrasaction="ignore")
    for row in reader:
        writer.writerow({c: row[c] for c in valid_columns})
    filtered.seek(0)

    cur.copy_expert(f'COPY "{tmp}" ({col_list}) FROM STDIN WITH CSV', filtered)
    conn.commit()  # commit temp table so it survives a rollback on the INSERT

    # Build WHERE clauses to pre-filter rows that would violate FK constraints.
    # e.g. inventories.set_num must exist in sets.set_num
    # Self-referential FKs are skipped (data is internally consistent within the CSV).
    # Nullable FK columns allow NULL through since NULL never violates a FK constraint.
    fk_filters = get_fk_filters(cur, table_name)
    where_clauses = [
        (
            f'(t."{local_col}" IS NULL OR t."{local_col}" IN (SELECT "{foreign_col}" FROM "{foreign_table}"))'
            if is_nullable
            else f't."{local_col}" IN (SELECT "{foreign_col}" FROM "{foreign_table}")'
        )
        for local_col, foreign_table, foreign_col, is_nullable in fk_filters
        if local_col in valid_columns
    ]
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cur.execute(
        f'INSERT INTO "{table_name}" ({col_list}) '
        f'SELECT {col_list} FROM "{tmp}" t {where_sql} ON CONFLICT DO NOTHING'
    )
    inserted = cur.rowcount
    conn.commit()

    if where_clauses:
        # Count how many rows were skipped due to FK mismatches
        cur.execute(f'SELECT COUNT(*) FROM "{tmp}"')
        total = cur.fetchone()[0]
        skipped = total - inserted
        if skipped:
            print(f"  (skipped {skipped} rows with unresolvable foreign keys)")

    cur.execute(f'DROP TABLE IF EXISTS "{tmp}"')
    conn.commit()
    cur.close()
    print(f"  Imported {table_name} ({inserted} rows)")


def refresh_views(conn):
    cur = conn.cursor()
    print("Refreshing materialized views...")
    cur.execute("REFRESH MATERIALIZED VIEW set_parts_mv")
    cur.execute("REFRESH MATERIALIZED VIEW set_parts_agnostic_mv")
    conn.commit()
    cur.close()
    print("Done.")


def main():
    print(f"Connecting to DB ...")
    conn = psycopg2.connect(DB_URL)

    for table_name, url in DOWNLOADS:
        print(f"\n[{table_name}]")
        try:
            csv_bytes = download_csv(url)
            import_table(conn, table_name, csv_bytes)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            conn.rollback()

    refresh_views(conn)
    conn.close()
    print("\nImport complete!")


if __name__ == "__main__":
    main()
