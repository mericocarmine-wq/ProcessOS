from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from app.commercial.application.service import (
    CommercialAuthorizationError,
    CommercialNotFoundError,
)
from app.commercial.domain.discovery import (
    DiscoveryRecord,
    normalize_domain,
    normalize_name,
    normalize_phone,
)
from app.commercial.domain.research import FetchedPage, analyze_website
from app.commercial.persistence.models import (
    Activity,
    Company,
    CompanySource,
    DiscoveryJob,
    Opportunity,
    ResearchJob,
    Signal,
    WebsiteAnalysis,
)
from app.commercial.persistence.repository import SqlAlchemyCommercialRepository
from app.core.application.auth import AuthenticatedIdentity


class WebsiteFetcher(Protocol):
    async def fetch(self, url: str) -> FetchedPage: ...


@dataclass(frozen=True, slots=True)
class DiscoveryOutcome:
    job: DiscoveryJob
    companies: list[Company]


class DiscoveryService:
    def __init__(
        self,
        repository: SqlAlchemyCommercialRepository,
        identity: AuthenticatedIdentity,
        fetcher: WebsiteFetcher,
    ) -> None:
        self._repository = repository
        self._identity = identity
        self._fetcher = fetcher

    def _authorize(self, permission: str) -> None:
        if permission not in self._identity.permissions:
            raise CommercialAuthorizationError(f"Missing permission: {permission}")

    async def import_records(
        self, records: list[DiscoveryRecord], provider: str = "csv"
    ) -> DiscoveryOutcome:
        self._authorize("commercial.write")
        job = DiscoveryJob(
            organization_id=self._identity.organization_id,
            source_type=provider,
            status="running",
        )
        self._repository.add(job)
        await self._repository.flush()
        created: list[Company] = []
        for record in records:
            try:
                domain = normalize_domain(record.domain)
                phone = normalize_phone(record.phone)
                duplicate = await self._repository.find_duplicate(
                    domain=domain,
                    phone=phone,
                    name=normalize_name(record.name),
                    city=record.city,
                    provider=provider,
                    external_id=record.external_id,
                )
                job.processed_count += 1
                if duplicate:
                    job.duplicate_count += 1
                    continue
                company = Company(
                    organization_id=self._identity.organization_id,
                    name=record.name.strip(),
                    domain=domain,
                    phone=phone,
                    email=record.email,
                    city=record.city,
                    source=provider,
                )
                self._repository.add(company)
                await self._repository.flush()
                self._repository.add(
                    Opportunity(
                        organization_id=self._identity.organization_id,
                        company_id=company.id,
                        stage="discovered",
                        next_best_action="Investigar empresa",
                        next_action_at=datetime.now(UTC) + timedelta(days=1),
                    )
                )
                self._repository.add(
                    CompanySource(
                        organization_id=self._identity.organization_id,
                        company_id=company.id,
                        provider=provider,
                        external_id=record.external_id,
                    )
                )
                self._repository.add(
                    Activity(
                        organization_id=self._identity.organization_id,
                        company_id=company.id,
                        actor_id=self._identity.user_id,
                        kind="discovered",
                        summary=f"Empresa descubierta mediante {provider}",
                        created_at=datetime.now(UTC),
                    )
                )
                job.created_count += 1
                created.append(company)
            except (ValueError, TypeError):
                job.processed_count += 1
                job.failed_count += 1
        job.status = "completed_with_errors" if job.failed_count else "completed"
        self._repository.record("commercial.discovery_completed", "discovery_job", job.id)
        await self._repository.commit()
        return DiscoveryOutcome(job, created)

    async def research(self, company_id: UUID) -> ResearchJob:
        self._authorize("commercial.write")
        company = await self._repository.get_company(company_id)
        if company is None:
            raise CommercialNotFoundError("Company not found")
        job = ResearchJob(
            organization_id=self._identity.organization_id,
            company_id=company_id,
            status="running",
            attempts=1,
        )
        self._repository.add(job)
        await self._repository.flush()
        try:
            if not company.domain:
                raise ValueError("Company has no domain")
            page = await self._fetcher.fetch(f"https://{company.domain}")
            result = analyze_website(page.content)
            self._repository.add(
                WebsiteAnalysis(
                    organization_id=self._identity.organization_id,
                    company_id=company_id,
                    url=page.url,
                    title=result.title,
                    observed=result.observed,
                    hypotheses=result.hypotheses,
                )
            )
            for code, value, confidence in result.signals:
                self._repository.add(
                    Signal(
                        organization_id=self._identity.organization_id,
                        company_id=company_id,
                        code=code,
                        evidence_type="observed",
                        value=value,
                        confidence=confidence,
                        source_url=page.url,
                    )
                )
            company.qualification_score = min(
                100, sum(10 for item in result.observed.values() if item is True)
            )
            if company.opportunity:
                company.opportunity.stage = "researched"
                company.opportunity.next_best_action = "Revisar señales y cualificar"
            job.status = "completed"
            self._repository.add(
                Activity(
                    organization_id=self._identity.organization_id,
                    company_id=company_id,
                    actor_id=self._identity.user_id,
                    kind="researched",
                    summary="Sitio web analizado y señales añadidas",
                    created_at=datetime.now(UTC),
                )
            )
        except Exception as exc:
            job.status = "failed"
            job.error_code = type(exc).__name__[:80]
        self._repository.record("commercial.research_finished", "research_job", job.id)
        await self._repository.commit()
        return job

    async def evidence(self, company_id: UUID) -> tuple[WebsiteAnalysis | None, list[Signal]]:
        self._authorize("commercial.read")
        if await self._repository.get_company(company_id) is None:
            raise CommercialNotFoundError("Company not found")
        return (
            await self._repository.latest_research(company_id),
            await self._repository.list_signals(company_id),
        )

    async def jobs(self) -> list[DiscoveryJob]:
        self._authorize("commercial.read")
        return await self._repository.list_discovery_jobs()
