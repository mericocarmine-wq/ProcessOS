from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.commercial.persistence.models import (
    Activity,
    Call,
    Company,
    CompanySource,
    DiscoveryJob,
    Opportunity,
    ResearchJob,
    Signal,
    WebsiteAnalysis,
)
from app.core.domain.context import OrganizationContext
from app.core.persistence.models import AuditEvent


class SqlAlchemyCommercialRepository:
    def __init__(self, session: AsyncSession, context: OrganizationContext) -> None:
        self._session = session
        self._context = context

    async def list_companies(self) -> list[Company]:
        statement = (
            select(Company)
            .options(selectinload(Company.opportunity), selectinload(Company.contacts))
            .where(Company.organization_id == self._context.organization_id)
            .order_by(Company.created_at.desc())
        )
        return list((await self._session.scalars(statement)).all())

    async def get_company(self, company_id: UUID) -> Company | None:
        return cast(
            Company | None,
            await self._session.scalar(
                select(Company)
                .options(selectinload(Company.opportunity), selectinload(Company.contacts))
                .where(
                    Company.id == company_id,
                    Company.organization_id == self._context.organization_id,
                )
            ),
        )

    async def get_opportunity(self, company_id: UUID) -> Opportunity | None:
        return cast(
            Opportunity | None,
            await self._session.scalar(
                select(Opportunity).where(
                    Opportunity.company_id == company_id,
                    Opportunity.organization_id == self._context.organization_id,
                )
            ),
        )

    async def find_duplicate(
        self,
        *,
        domain: str | None,
        phone: str | None,
        name: str,
        city: str | None,
        provider: str,
        external_id: str | None,
    ) -> Company | None:
        conditions = []
        if domain:
            conditions.append(Company.domain == domain)
        if phone:
            conditions.append(Company.phone == phone)
        if city:
            conditions.append(
                (func.lower(Company.name) == name) & (func.lower(Company.city) == city.lower())
            )
        if external_id:
            source_company = await self._session.scalar(
                select(CompanySource.company_id).where(
                    CompanySource.organization_id == self._context.organization_id,
                    CompanySource.provider == provider,
                    CompanySource.external_id == external_id,
                )
            )
            if source_company:
                conditions.append(Company.id == source_company)
        if not conditions:
            return None
        from sqlalchemy import or_

        return cast(
            Company | None,
            await self._session.scalar(
                select(Company).where(
                    Company.organization_id == self._context.organization_id,
                    or_(*conditions),
                )
            ),
        )

    async def latest_research(self, company_id: UUID) -> WebsiteAnalysis | None:
        return cast(
            WebsiteAnalysis | None,
            await self._session.scalar(
                select(WebsiteAnalysis)
                .where(
                    WebsiteAnalysis.organization_id == self._context.organization_id,
                    WebsiteAnalysis.company_id == company_id,
                )
                .order_by(WebsiteAnalysis.created_at.desc())
            ),
        )

    async def list_signals(self, company_id: UUID) -> list[Signal]:
        return list(
            (
                await self._session.scalars(
                    select(Signal)
                    .where(
                        Signal.organization_id == self._context.organization_id,
                        Signal.company_id == company_id,
                    )
                    .order_by(Signal.created_at.desc())
                )
            ).all()
        )

    async def list_discovery_jobs(self) -> list[DiscoveryJob]:
        return list(
            (
                await self._session.scalars(
                    select(DiscoveryJob)
                    .where(DiscoveryJob.organization_id == self._context.organization_id)
                    .order_by(DiscoveryJob.created_at.desc())
                )
            ).all()
        )

    async def get_research_job(self, job_id: UUID) -> ResearchJob | None:
        return cast(
            ResearchJob | None,
            await self._session.scalar(
                select(ResearchJob).where(
                    ResearchJob.id == job_id,
                    ResearchJob.organization_id == self._context.organization_id,
                )
            ),
        )

    async def list_activities(self, company_id: UUID) -> list[Activity]:
        statement = (
            select(Activity)
            .where(
                Activity.company_id == company_id,
                Activity.organization_id == self._context.organization_id,
            )
            .order_by(Activity.created_at.desc())
        )
        return list((await self._session.scalars(statement)).all())

    async def due_opportunities(self, now: datetime) -> list[Opportunity]:
        statement = (
            select(Opportunity)
            .options(selectinload(Opportunity.company))
            .where(
                Opportunity.organization_id == self._context.organization_id,
                Opportunity.next_action_at.is_not(None),
                Opportunity.next_action_at <= now,
                Opportunity.stage.not_in(("won", "lost")),
            )
            .order_by(Opportunity.next_action_at)
        )
        return list((await self._session.scalars(statement)).all())

    async def count_calls_today(self, start: datetime) -> int:
        return int(
            await self._session.scalar(
                select(func.count(Call.id)).where(
                    Call.organization_id == self._context.organization_id,
                    Call.occurred_at >= start,
                )
            )
            or 0
        )

    def add(self, entity: object) -> None:
        self._session.add(entity)

    def record(self, action: str, resource_type: str, resource_id: UUID) -> None:
        self._session.add(
            AuditEvent(
                organization_id=self._context.organization_id,
                actor_id=self._context.actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id),
                result="success",
            )
        )

    async def flush(self) -> None:
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC)
