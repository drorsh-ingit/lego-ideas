import json
from datetime import datetime

import httpx
import psycopg2

from app.core.config import settings
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def identify_photo_task(self, photo_id: str, file_path: str):
    """
    Read the saved photo, call Brickognize API, store result.
    Uses synchronous DB access via psycopg2 (not asyncpg).
    """
    # Parse async DB URL to sync
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # Mark photo as processing
        cur.execute(
            "UPDATE session_photos SET status = 'processing', updated_at = %s WHERE id = %s",
            (datetime.utcnow(), photo_id),
        )

        # Read image
        with open(file_path, "rb") as f:
            image_bytes = f.read()

        # Call Brickognize
        response = httpx.post(
            f"{settings.brickognize_api_url}/predict/parts/",
            files={"query_image": ("photo.jpg", image_bytes, "image/jpeg")},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        # Store raw response, mark done
        cur.execute(
            "UPDATE session_photos SET status = 'done', raw_response = %s, updated_at = %s WHERE id = %s",
            (json.dumps(data), datetime.utcnow(), photo_id),
        )

    except Exception as exc:
        # Mark failed
        cur.execute(
            "UPDATE session_photos SET status = 'failed', updated_at = %s WHERE id = %s",
            (datetime.utcnow(), photo_id),
        )
        cur.close()
        conn.close()
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 5)

    cur.close()
    conn.close()
    return {"photo_id": photo_id, "status": "done"}
