#!/usr/bin/env python3
"""
Download Rebrickable CSV dumps and import them into PostgreSQL.
Usage: python scripts/import_rebrickable.py

Rebrickable CSV download URLs:
  https://cdn.rebrickable.com/media/downloads/themes.csv.gz
  https://cdn.rebrickable.com/media/downloads/colors.csv.gz
  https://cdn.rebrickable.com/media/downloads/part_categories.csv.gz
  https://cdn.rebrickable.com/media/downloads/parts.csv.gz
  https://cdn.rebrickable.com/media/downloads/part_relationships.csv.gz
  https://cdn.rebrickable.com/media/downloads/sets.csv.gz
  https://cdn.rebrickable.com/media/downloads/inventories.csv.gz
  https://cdn.rebrickable.com/media/downloads/inventory_parts.csv.gz
"""
import gzip
import io
import sys

import httpx
import psycopg2

# Override with your actual DB connection string
DB_URL = "postgresql://lego:legopass@localhost:5432/legoideas"

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


def import_table(conn, table_name: str, csv_bytes: bytes):
    cur = conn.cursor()
    # Truncate with CASCADE to handle FK constraints
    cur.execute(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE')
    conn.commit()

    f = io.StringIO(csv_bytes.decode("utf-8"))
    # Read and parse header
    header = f.readline()
    columns = [col.strip() for col in header.split(",")]

    cur.copy_expert(
        f'COPY "{table_name}" ({", ".join(columns)}) FROM STDIN WITH CSV',
        f,
    )
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
    print(f"Connecting to {DB_URL} ...")
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
