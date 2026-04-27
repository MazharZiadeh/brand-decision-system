import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from src.config import Settings, get_settings


def _configure_logging(settings: Settings) -> None:
    """Configure structlog to emit JSON to stdout at the configured level.

    CLAUDE.md §4.5 mandates structured JSON logs with `timestamp`, `level`, `event`
    on every entry; `session_id` flows in as a contextvar once Session 2+ wires it.
    """
    level = getattr(logging, settings.log_level)
    logging.basicConfig(format="%(message)s", level=level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _configure_logging(settings)
    log = structlog.get_logger()
    log.info("app.start", service="brand-decision-system", app_env=settings.app_env)
    try:
        yield
    finally:
        log.info("app.shutdown", service="brand-decision-system")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Brand Decision System",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "brand-decision-system"}

    return app


app = create_app()
