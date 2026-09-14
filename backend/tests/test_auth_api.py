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

        second_registration = await client.post(
            "/auth/register",
            json={
                "email": "second-owner@example.com",
                "password": f"Second-{uuid4()}!",
                "organization_name": "Tenant B",
                "organization_slug": "tenant-b",
            },
        )
        assert second_registration.status_code == 201
        add_member = await client.post(
            "/core/members",
            headers=headers,
            json={"email": "second-owner@example.com", "role": "viewer"},
        )
        assert add_member.status_code == 201
        members = await client.get("/core/members", headers=headers)
        assert members.status_code == 200
        assert {member["email"] for member in members.json()} == {
            "owner@example.com",
            "second-owner@example.com",
        }
        owner_membership = next(
            member for member in members.json() if member["email"] == "owner@example.com"
        )
        last_owner_change = await client.patch(
            f"/core/members/{owner_membership['id']}/role",
            headers=headers,
            json={"role": "manager"},
        )
        assert last_owner_change.status_code == 409

        flag_update = await client.put(
            "/core/feature-flags/new-dashboard",
            headers=headers,
            json={"enabled": True},
        )
        assert flag_update.status_code == 204
        flags = await client.get("/core/feature-flags", headers=headers)
        assert flags.json() == [{"key": "new-dashboard", "enabled": True}]

        audit_events = await client.get("/core/audit-events", headers=headers)
        assert audit_events.status_code == 200
        assert any(event["action"] == "membership.created" for event in audit_events.json())

        logout = await client.post("/auth/logout", headers=headers)
        assert logout.status_code == 204
        assert (await client.get("/auth/me", headers=headers)).status_code == 401

    await engine.dispose()
