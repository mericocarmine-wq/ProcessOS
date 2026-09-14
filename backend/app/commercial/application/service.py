from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.commercial.domain.enums import CallOutcome, PipelineStage
from app.commercial.domain.rules import require_next_action
from app.commercial.persistence.models import Activity, Call, Company, Opportunity
from app.commercial.persistence.repository import SqlAlchemyCommercialRepository
from app.core.application.auth import AuthenticatedIdentity
from app.core.exceptions import ProcessOSError


class CommercialAuthorizationError(ProcessOSError):
    pass


class CommercialNotFoundError(ProcessOSError):
    pass


@dataclass(frozen=True, slots=True)
class TodaySummary:
    calls_completed: int
    overdue_actions: int
    hot_leads: int
    next_actions: list[Opportunity]


class CommercialService:
    def __init__(
        self, repository: SqlAlchemyCommercialRepository, identity: AuthenticatedIdentity
    ) -> None:
        self._repository = repository
        self._identity = identity

    def _authorize(self, permission: str) -> None:
        if permission not in self._identity.permissions:
            raise CommercialAuthorizationError(f"Missing permission: {permission}")

    async def list_companies(self) -> list[Company]:
        self._authorize("commercial.read")
        return await self._repository.list_companies()

    async def get_company(self, company_id: UUID) -> tuple[Company, list[Activity]]:
        self._authorize("commercial.read")
        company = await self._repository.get_company(company_id)
        if company is None:
            raise CommercialNotFoundError("Company not found")
        return company, await self._repository.list_activities(company_id)

    async def create_company(
        self,
        *,
        name: str,
        domain: str | None,
        phone: str | None,
        email: str | None,
        city: str | None,
        next_best_action: str,
        next_action_at: datetime,
    ) -> Company:
        self._authorize("commercial.write")
        require_next_action(PipelineStage.DISCOVERED, next_best_action, next_action_at)
        company = Company(
            organization_id=self._identity.organization_id,
            name=name,
            domain=domain,
            phone=phone,
            email=email,
            city=city,
        )
        self._repository.add(company)
        await self._repository.flush()
        opportunity = Opportunity(
            organization_id=self._identity.organization_id,
            company_id=company.id,
            stage=PipelineStage.DISCOVERED.value,
            next_best_action=next_best_action,
            next_action_at=next_action_at,
        )
        self._repository.add(opportunity)
        self._repository.add(
            Activity(
                organization_id=self._identity.organization_id,
                company_id=company.id,
                actor_id=self._identity.user_id,
                kind="company_created",
                summary="Empresa añadida manualmente al pipeline",
                created_at=datetime.now(UTC),
            )
        )
        self._repository.record("commercial.company_created", "company", company.id)
        await self._repository.commit()
        company.opportunity = opportunity
        return company

    async def move_stage(
        self,
        company_id: UUID,
        stage: PipelineStage,
        next_best_action: str | None,
        next_action_at: datetime | None,
    ) -> Opportunity:
        self._authorize("commercial.write")
        require_next_action(stage, next_best_action, next_action_at)
        opportunity = await self._repository.get_opportunity(company_id)
        if opportunity is None:
            raise CommercialNotFoundError("Opportunity not found")
        previous = opportunity.stage
        opportunity.stage = stage.value
        opportunity.next_best_action = None if stage.is_terminal else next_best_action
        opportunity.next_action_at = None if stage.is_terminal else next_action_at
        self._repository.add(
            Activity(
                organization_id=self._identity.organization_id,
                company_id=company_id,
                actor_id=self._identity.user_id,
                kind="stage_changed",
                summary=f"Etapa cambiada de {previous} a {stage.value}",
                created_at=datetime.now(UTC),
            )
        )
        self._repository.record("commercial.stage_changed", "company", company_id)
        await self._repository.commit()
        return opportunity

    async def register_call(
        self,
        company_id: UUID,
        outcome: CallOutcome,
        notes: str | None,
        next_best_action: str | None,
        next_action_at: datetime | None,
    ) -> Call:
        self._authorize("commercial.write")
        opportunity = await self._repository.get_opportunity(company_id)
        if opportunity is None:
            raise CommercialNotFoundError("Company not found")
        require_next_action(PipelineStage(opportunity.stage), next_best_action, next_action_at)
        opportunity.next_best_action = next_best_action
        opportunity.next_action_at = next_action_at
        now = datetime.now(UTC)
        call = Call(
            organization_id=self._identity.organization_id,
            company_id=company_id,
            actor_id=self._identity.user_id,
            outcome=outcome.value,
            notes=notes,
            occurred_at=now,
        )
        self._repository.add(call)
        self._repository.add(
            Activity(
                organization_id=self._identity.organization_id,
                company_id=company_id,
                actor_id=self._identity.user_id,
                kind="call",
                summary=f"Llamada registrada: {outcome.value}",
                created_at=now,
            )
        )
        self._repository.record("commercial.call_registered", "company", company_id)
        await self._repository.commit()
        return call

    async def today(self) -> TodaySummary:
        self._authorize("commercial.read")
        now = datetime.now(UTC)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        actions = await self._repository.due_opportunities(now)
        return TodaySummary(
            calls_completed=await self._repository.count_calls_today(start),
            overdue_actions=len(actions),
            hot_leads=sum(1 for item in actions if item.company.qualification_score >= 70),
            next_actions=actions,
        )
