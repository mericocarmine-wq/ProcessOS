from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.commercial.persistence.models import Activity, Call, Company, Opportunity
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
