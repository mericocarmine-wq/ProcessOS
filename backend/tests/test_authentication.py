from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.application.auth import AuthenticationError, AuthService, InvalidRecoveryTokenError
from app.core.config import Settings
from app.core.persistence.auth_repository import SqlAlchemyAuthRepository
from app.core.persistence.base import Base
from app.core.persistence.models import AuthSession, Organization
from app.core.security import TokenService, hash_token


class CapturingRecoveryDelivery:
    def __init__(self) -> None:
        self.reset_url: str | None = None

    async def send(self, *, email: str, reset_url: str) -> None:
        self.reset_url = reset_url


async def test_session_lifecycle_and_tenant_claim_validation() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessions = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(
        environment="test",
        jwt_secret=SecretStr("test-secret-that-is-longer-than-thirty-two-characters"),
    )
    tokens = TokenService(settings)
    valid_credential = f"Test-{uuid4()}!"

    async with sessions() as session:
        service = AuthService(SqlAlchemyAuthRepository(session), tokens)
        user, organization = await service.register_owner(
            email="owner@example.com",
            password=valid_credential,
            organization_name="Tenant A",
            organization_slug="tenant-a",
        )
        issued = await service.login(
            email=user.email,
            password=valid_credential,
            organization_slug=organization.slug,
        )
        identity = await service.authenticate(issued.access_token)

        assert identity.organization_id == organization.id
        assert identity.role == "owner"

        other_organization = Organization(name="Tenant B", slug="tenant-b")
        session.add(other_organization)
        await session.commit()
        forged_session_id = uuid4()
        forged_scope_token, forged_expiry = tokens.create(
            user_id=identity.user_id,
            organization_id=other_organization.id,
            membership_id=identity.membership_id,
            session_id=forged_session_id,
            role=identity.role,
        )
        session.add(
            AuthSession(
                id=forged_session_id,
                user_id=identity.user_id,
                token_hash=hash_token(forged_scope_token),
                expires_at=forged_expiry,
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()

        with pytest.raises(AuthenticationError):
            await service.authenticate(forged_scope_token)

        await service.logout(identity)
        with pytest.raises(AuthenticationError):
            await service.authenticate(issued.access_token)

    await engine.dispose()


async def test_invalid_password_does_not_issue_session() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessions = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(
        environment="test",
        jwt_secret=SecretStr("test-secret-that-is-longer-than-thirty-two-characters"),
    )
    valid_credential = f"Test-{uuid4()}!"
    async with sessions() as session:
        service = AuthService(SqlAlchemyAuthRepository(session), TokenService(settings))
        await service.register_owner(
            email="owner@example.com",
            password=valid_credential,
            organization_name="Tenant A",
            organization_slug="tenant-a",
        )

        with pytest.raises(AuthenticationError):
            await service.login(
                email="owner@example.com",
                password=uuid4().hex,
                organization_slug="tenant-a",
            )

    await engine.dispose()


async def test_password_reset_is_single_use_and_revokes_sessions() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(
        environment="test",
        jwt_secret=SecretStr("test-secret-that-is-longer-than-thirty-two-characters"),
    )
    delivery = CapturingRecoveryDelivery()
    original_credential = f"Original-{uuid4()}!"
    new_credential = f"Replacement-{uuid4()}!"

    async with sessions() as session:
        service = AuthService(
            SqlAlchemyAuthRepository(session),
            TokenService(settings),
            recovery_delivery=delivery,
        )
        await service.register_owner(
            email="recovery@example.com",
            password=original_credential,
            organization_name="Recovery Tenant",
            organization_slug="recovery-tenant",
        )
        issued = await service.login(
            email="recovery@example.com",
            password=original_credential,
            organization_slug="recovery-tenant",
        )
        await service.request_password_reset("recovery@example.com")
        assert delivery.reset_url is not None
        raw_token = parse_qs(urlparse(delivery.reset_url).query)["token"][0]

        await service.reset_password(raw_token, new_credential)
        with pytest.raises(AuthenticationError):
            await service.authenticate(issued.access_token)
        with pytest.raises(InvalidRecoveryTokenError):
            await service.reset_password(raw_token, new_credential)

        replacement = await service.login(
            email="recovery@example.com",
            password=new_credential,
            organization_slug="recovery-tenant",
        )
        assert replacement.access_token

    await engine.dispose()
