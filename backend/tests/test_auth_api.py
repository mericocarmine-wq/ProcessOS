from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.health import get_session
from app.core.config import Settings
from app.core.persistence.base import Base
from app.main import create_app


async def test_register_login_me_and_logout_api_flow() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    settings = Settings(
        environment="test",
        jwt_secret=SecretStr("test-secret-that-is-longer-than-thirty-two-characters"),
    )
    application = create_app(settings)

    async def override_session():  # type: ignore[no-untyped-def]
        async with sessions() as session:
            yield session

    application.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=application)
    valid_credential = f"Test-{uuid4()}!"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        registration = await client.post(
            "/auth/register",
            json={
                "email": "owner@example.com",
                "password": valid_credential,
                "organization_name": "Tenant A",
                "organization_slug": "tenant-a",
            },
        )
        assert registration.status_code == 201

        login = await client.post(
            "/auth/login",
            json={
                "email": "owner@example.com",
                "password": valid_credential,
                "organization_slug": "tenant-a",
            },
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        profile = await client.get("/auth/me", headers=headers)
        assert profile.status_code == 200
        assert profile.json()["role"] == "owner"
        assert "apps.manage" in profile.json()["permissions"]
        assert profile.json()["organization_id"] == registration.json()["organization_id"]

        initial_apps = await client.get("/core/apps", headers=headers)
        assert initial_apps.status_code == 200
        assert [app["code"] for app in initial_apps.json()] == ["core"]

        enable_finance = await client.put(
            "/core/apps/finance",
            headers=headers,
            json={"enabled": True},
        )
        assert enable_finance.status_code == 204
        enabled_apps = await client.get("/core/apps", headers=headers)
        assert {app["code"] for app in enabled_apps.json()} == {"core", "finance"}

        disable_core = await client.put(
            "/core/apps/core",
            headers=headers,
            json={"enabled": False},
        )
        assert disable_core.status_code == 409

        logout = await client.post("/auth/logout", headers=headers)
        assert logout.status_code == 204
        assert (await client.get("/auth/me", headers=headers)).status_code == 401

    await engine.dispose()
