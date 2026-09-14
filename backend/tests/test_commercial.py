from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.commercial.application.service import CommercialService
from app.commercial.domain.enums import PipelineStage
from app.commercial.domain.rules import CommercialRuleViolation, require_next_action
from app.commercial.persistence.models import Company, Opportunity
from app.commercial.persistence.repository import SqlAlchemyCommercialRepository
from app.core.application.auth import AuthenticatedIdentity
from app.core.domain.context import OrganizationContext
from app.core.persistence.base import Base
from app.core.persistence.models import Organization, User


def test_active_opportunity_requires_next_action() -> None:
    with pytest.raises(CommercialRuleViolation):
        require_next_action(PipelineStage.QUALIFIED, None, None)
    require_next_action(PipelineStage.WON, None, None)


async def test_company_repository_isolates_tenants() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        first = Organization(name="First", slug="first")
        second = Organization(name="Second", slug="second")
        actor = User(email="owner@example.com", password_hash=uuid4().hex)
        session.add_all([first, second, actor])
        await session.flush()
        companies = [
            Company(organization_id=first.id, name="Visible"),
            Company(organization_id=second.id, name="Hidden"),
        ]
        session.add_all(companies)
        await session.flush()
        session.add_all(
            [
                Opportunity(
                    organization_id=item.organization_id,
                    company_id=item.id,
                    stage="discovered",
                    next_best_action="Call",
                    next_action_at=datetime.now(UTC),
                )
                for item in companies
            ]
        )
        await session.commit()
        context = OrganizationContext(first.id, actor.id)
        visible = await SqlAlchemyCommercialRepository(session, context).list_companies()
    assert [company.name for company in visible] == ["Visible"]
    await engine.dispose()


async def test_pipeline_can_reach_won_and_records_activity() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        organization = Organization(name="Sales", slug="sales")
        actor = User(email="sales@example.com", password_hash=uuid4().hex)
        session.add_all([organization, actor])
        await session.flush()
        identity = AuthenticatedIdentity(
            user_id=actor.id,
            email=actor.email,
            organization_id=organization.id,
            organization_name=organization.name,
            membership_id=uuid4(),
            role="owner",
            permissions=frozenset({"commercial.read", "commercial.write"}),
            session_id=uuid4(),
        )
        service = CommercialService(
            SqlAlchemyCommercialRepository(session, OrganizationContext(organization.id, actor.id)),
            identity,
        )
        company = await service.create_company(
            name="Acme",
            domain="acme.test",
            phone=None,
            email=None,
            city=None,
            next_best_action="Research buyer",
            next_action_at=datetime.now(UTC) + timedelta(days=1),
        )
        won = await service.move_stage(company.id, PipelineStage.WON, None, None)
        _, activities = await service.get_company(company.id)
    assert won.stage == "won"
    assert [activity.kind for activity in activities] == ["stage_changed", "company_created"]
    await engine.dispose()
