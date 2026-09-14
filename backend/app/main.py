from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.commercial import router as commercial_router
from app.api.core import router as core_router
from app.api.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.logging import configure_logging
from app.core.security import normalize_allowed_origins


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.database = Database(runtime_settings)
        yield
        await application.state.database.close()

    application = FastAPI(
        title=runtime_settings.app_name,
        version="0.1.0",
        docs_url="/docs" if runtime_settings.environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    application.state.settings = runtime_settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=normalize_allowed_origins(runtime_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(core_router)
    application.include_router(commercial_router)
    return application


app = create_app()
