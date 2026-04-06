"""
FastAPI application entry point.
Real Estate CRM Automation Agent by Datawebify.
"""

import uvicorn
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import qualification, webhooks, health
from app.utils.config import settings
from app.utils.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    setup_logging(settings.LOG_LEVEL)
    logger = structlog.get_logger(__name__)
    logger.info("app_starting", environment=settings.APP_ENV)
    yield
    logger.info("app_shutting_down")


app = FastAPI(
    title="RE CRM Automation Agent",
    description="Real Estate Wholesaling CRM Automation powered by GPT-4o and GoHighLevel",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(qualification.router)
app.include_router(webhooks.router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development",
    )