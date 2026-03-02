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

    # Insert ignoring duplicates; for FK violations (e.g. fig- inventories)
    # wrap each row individually so one bad row doesn't abort the whole import
    try:
        cur.execute(
            f'INSERT INTO "{table_name}" ({col_list}) SELECT {col_list} FROM "{tmp}" ON CONFLICT DO NOTHING'
        )
        conn.commit()
    except Exception:
        conn.rollback()
        # Fall back to savepoint-per-row (single transaction, skips FK violations)
        cur2 = conn.cursor()
        cur2.execute(f'SELECT {col_list} FROM "{tmp}"')
        rows = cur2.fetchall()
        cur2.close()
        inserted = 0
        placeholders = ", ".join(["%s"] * len(valid_columns))
        insert_sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
        cur3 = conn.cursor()
        for row in rows:
            cur3.execute("SAVEPOINT sp")
            try:
                cur3.execute(insert_sql, row)
                cur3.execute("RELEASE SAVEPOINT sp")
                inserted += 1
            except Exception:
                cur3.execute("ROLLBACK TO SAVEPOINT sp")
                cur3.execute("RELEASE SAVEPOINT sp")
        conn.commit()  # single commit for all rows
        cur3.close()
        print(f"  (savepoint fallback: {inserted}/{len(rows)} rows inserted)")

    cur.execute(f'DROP TABLE IF EXISTS "{tmp}"')
    conn.commit()
    cur.close()
    print(f"  Imported {table_name}")


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
