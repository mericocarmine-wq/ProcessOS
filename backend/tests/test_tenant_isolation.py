from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.domain.context import OrganizationContext
from app.core.persistence.audit_repository import SqlAlchemyAuditEventRepository
from app.core.persistence.base import Base
from app.core.persistence.models import AuditEvent, Organization, User


async def test_audit_repository_never_reads_another_tenant() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        organization_a = Organization(name="Tenant A", slug="tenant-a")
        organization_b = Organization(name="Tenant B", slug="tenant-b")
        actor = User(email="owner@example.com", password_hash=uuid4().hex)
        session.add_all([organization_a, organization_b, actor])
        await session.flush()
        session.add_all(
            [
                AuditEvent(
                    organization_id=organization_a.id,
                    actor_id=actor.id,
                    action="company.read",
                    resource_type="company",
                    result="success",
                    created_at=datetime.now(UTC),
                ),
                AuditEvent(
                    organization_id=organization_b.id,
                    actor_id=actor.id,
                    action="private.other-tenant",
                    resource_type="company",
                    result="success",
                    created_at=datetime.now(UTC),
                ),
            ]
        )
        await session.commit()

        context = OrganizationContext(organization_id=organization_a.id, actor_id=actor.id)
        events = await SqlAlchemyAuditEventRepository(session, context).list()

    assert [event.action for event in events] == ["company.read"]
    assert all(event.organization_id == organization_a.id for event in events)
    await engine.dispose()
