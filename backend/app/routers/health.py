"""Liveness and readiness probes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse, CamelModel

router = APIRouter(tags=["health"])


class HealthOut(CamelModel):
    status: str
    database: str
    server_time: datetime


@router.get("/health", response_model=ApiResponse[HealthOut], summary="Liveness probe")
async def health(db: AsyncSession = Depends(get_db)) -> ApiResponse[HealthOut]:
    try:
        await db.execute(text("SELECT 1"))
        database = "up"
    except Exception:
        database = "down"

    return ApiResponse(
        data=HealthOut(
            status="ok" if database == "up" else "degraded",
            database=database,
            server_time=datetime.now(UTC),
        )
    )