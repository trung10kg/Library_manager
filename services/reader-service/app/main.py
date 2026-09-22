from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import router as api_router
from app.core.config import settings
from common.db import configure_database, dispose_database
from common.errors import register_error_handlers
from common.health import add_health_routes

API_PREFIX = "/api/readers"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logging.basicConfig(level=settings.LOG_LEVEL)
    configure_database(settings.DATABASE_URL)
    yield
    await dispose_database()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Reader Service",
        version="0.1.0",
        lifespan=lifespan,
        # Docs nam duoi prefix de mo duoc qua gateway.
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
        redoc_url=None,
    )
    register_error_handlers(app)
    add_health_routes(app, API_PREFIX, settings.SERVICE_NAME)
    app.include_router(api_router, prefix=API_PREFIX)
    return app


app = create_app()
