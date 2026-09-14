from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.health import get_session
from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def app():  # type: ignore[no-untyped-def]
    application = create_app(Settings(environment="test"))
    session = AsyncMock(spec=AsyncSession)

    async def override_session() -> AsyncSession:
        return session

    application.dependency_overrides[get_session] = override_session
    return application, session


async def test_health_does_not_require_database(app) -> None:  # type: ignore[no-untyped-def]
    application, _ = app
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_checks_database(app) -> None:  # type: ignore[no-untyped-def]
    application, session = app
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    session.execute.assert_awaited_once()
