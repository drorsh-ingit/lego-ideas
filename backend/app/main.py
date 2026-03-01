from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import bom, matching, photos, reference, sessions
from app.core.config import settings


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Lego Set Matcher API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api/v1")
app.include_router(photos.router, prefix="/api/v1")
app.include_router(bom.router, prefix="/api/v1")
app.include_router(matching.router, prefix="/api/v1")
app.include_router(reference.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
