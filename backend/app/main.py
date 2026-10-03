"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import dispose_engine
from app.core.errors import register_exception_handlers
from app.routers import api_routers

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("%s starting", settings.app_name)
    yield
    await dispose_engine()
    logger.info("%s stopped", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Banking API for the BankDash dashboard. Every endpoint returns the same "
        "envelope: `{success, message, data}`. Authenticate with "
        "`POST /api/v1/auth/login` and send the access token as "
        "`Authorization: Bearer <token>`."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

for router in api_routers:
    app.include_router(router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }