from datetime import datetime
from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import CurrentIdentity
from app.api.health import get_session
from app.commercial.application.discovery import DiscoveryService
from app.commercial.application.service import (
    CommercialAuthorizationError,
    CommercialNotFoundError,
    CommercialService,
)
from app.commercial.domain.discovery import DiscoveryRecord
from app.commercial.domain.enums import PIPELINE_ORDER, CallOutcome, PipelineStage
from app.commercial.domain.rules import CommercialRuleViolation
from app.commercial.infrastructure.web_fetcher import SafeWebsiteFetcher
from app.commercial.persistence.models import Company
from app.commercial.persistence.repository import SqlAlchemyCommercialRepository
from app.core.domain.context import OrganizationContext

router = APIRouter(prefix="/commercial", tags=["commercial"])
Session = Annotated[AsyncSession, Depends(get_session)]


class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    domain: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    city: str | None = Field(default=None, max_length=120)
    next_best_action: str = Field(min_length=2, max_length=255)
    next_action_at: datetime


class OpportunityResponse(BaseModel):
    stage: PipelineStage
    value: float | None
    next_best_action: str | None
    next_action_at: datetime | None


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    domain: str | None
    phone: str | None
    email: str | None
    city: str | None
    source: str
    qualification_score: int
    opportunity: OpportunityResponse

    @classmethod
    def from_entity(cls, company: Company) -> "CompanyResponse":
        return cls(
            id=company.id,
            name=company.name,
            domain=company.domain,
            phone=company.phone,
            email=company.email,
            city=company.city,
            source=company.source,
            qualification_score=company.qualification_score,
            opportunity=OpportunityResponse.model_validate(
                company.opportunity, from_attributes=True
            ),
        )


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    kind: str
    summary: str
    created_at: datetime


class CompanyDetailResponse(CompanyResponse):
    activities: list[ActivityResponse]


class StageUpdate(BaseModel):
    stage: PipelineStage
    next_best_action: str | None = Field(default=None, max_length=255)
    next_action_at: datetime | None = None


class CallCreate(BaseModel):
    outcome: CallOutcome
    notes: str | None = Field(default=None, max_length=5000)
    next_best_action: str | None = Field(default=None, max_length=255)
    next_action_at: datetime | None = None


class NextActionResponse(BaseModel):
    company_id: UUID
    company_name: str
    stage: PipelineStage
    action: str
    due_at: datetime


class TodayResponse(BaseModel):
    calls_completed: int
    overdue_actions: int
    hot_leads: int
    next_actions: list[NextActionResponse]


def build_commercial(session: Session, identity: CurrentIdentity) -> CommercialService:
    context = OrganizationContext(identity.organization_id, identity.user_id)
    return CommercialService(SqlAlchemyCommercialRepository(session, context), identity)


Commercial = Annotated[CommercialService, Depends(build_commercial)]


def build_discovery(session: Session, identity: CurrentIdentity) -> DiscoveryService:
    context = OrganizationContext(identity.organization_id, identity.user_id)
    return DiscoveryService(
        SqlAlchemyCommercialRepository(session, context), identity, SafeWebsiteFetcher()
    )


Discovery = Annotated[DiscoveryService, Depends(build_discovery)]


class DiscoveryRecordRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    domain: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    external_id: str | None = Field(default=None, max_length=255)


class DiscoveryImportRequest(BaseModel):
    provider: str = Field(default="csv", pattern=r"^[a-z0-9_-]+$", max_length=30)
    records: list[DiscoveryRecordRequest] = Field(min_length=1, max_length=500)


class DiscoveryJobResponse(BaseModel):
    id: UUID
    source_type: str
    status: str
    processed_count: int
    created_count: int
    duplicate_count: int
    failed_count: int


class ResearchJobResponse(BaseModel):
    id: UUID
    company_id: UUID
    status: str
    attempts: int
    error_code: str | None


class SignalResponse(BaseModel):
    code: str
    evidence_type: str
    value: str
    confidence: int
    source_url: str | None


class EvidenceResponse(BaseModel):
    observed: dict[str, object]
    hypotheses: dict[str, object]
    signals: list[SignalResponse]


def raise_commercial_error(exc: Exception) -> NoReturn:
    if isinstance(exc, CommercialAuthorizationError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if isinstance(exc, CommercialNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, CommercialRuleViolation):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    raise exc


@router.get("/pipeline-stages", response_model=list[PipelineStage])
async def pipeline_stages(identity: CurrentIdentity) -> list[PipelineStage]:
    if "commercial.read" not in identity.permissions:
        raise HTTPException(status_code=403, detail="Missing permission")
    return list(PIPELINE_ORDER)


@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies(commercial: Commercial) -> list[CompanyResponse]:
    try:
        return [CompanyResponse.from_entity(item) for item in await commercial.list_companies()]
    except (CommercialAuthorizationError, CommercialNotFoundError, CommercialRuleViolation) as exc:
        raise_commercial_error(exc)


@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(payload: CompanyCreate, commercial: Commercial) -> CompanyResponse:
    try:
        company = await commercial.create_company(**payload.model_dump())
        return CompanyResponse.from_entity(company)
    except (CommercialAuthorizationError, CommercialNotFoundError, CommercialRuleViolation) as exc:
        raise_commercial_error(exc)


@router.get("/companies/{company_id}", response_model=CompanyDetailResponse)
async def get_company(company_id: UUID, commercial: Commercial) -> CompanyDetailResponse:
    try:
        company, activities = await commercial.get_company(company_id)
        base = CompanyResponse.from_entity(company).model_dump()
        return CompanyDetailResponse(
            **base,
            activities=[ActivityResponse.model_validate(item) for item in activities],
        )
    except (CommercialAuthorizationError, CommercialNotFoundError, CommercialRuleViolation) as exc:
        raise_commercial_error(exc)


@router.patch("/companies/{company_id}/stage", response_model=OpportunityResponse)
async def move_stage(
    company_id: UUID, payload: StageUpdate, commercial: Commercial
) -> OpportunityResponse:
    try:
        opportunity = await commercial.move_stage(company_id, **payload.model_dump())
        return OpportunityResponse.model_validate(opportunity, from_attributes=True)
    except (CommercialAuthorizationError, CommercialNotFoundError, CommercialRuleViolation) as exc:
        raise_commercial_error(exc)


@router.post("/companies/{company_id}/calls", status_code=status.HTTP_201_CREATED)
async def register_call(
    company_id: UUID, payload: CallCreate, commercial: Commercial
) -> dict[str, str]:
    try:
        call = await commercial.register_call(company_id, **payload.model_dump())
        return {"id": str(call.id), "outcome": call.outcome}
    except (CommercialAuthorizationError, CommercialNotFoundError, CommercialRuleViolation) as exc:
        raise_commercial_error(exc)


@router.get("/today", response_model=TodayResponse)
async def today(commercial: Commercial) -> TodayResponse:
    try:
        summary = await commercial.today()
        return TodayResponse(
            calls_completed=summary.calls_completed,
            overdue_actions=summary.overdue_actions,
            hot_leads=summary.hot_leads,
            next_actions=[
                NextActionResponse(
                    company_id=item.company_id,
                    company_name=item.company.name,
                    stage=PipelineStage(item.stage),
                    action=item.next_best_action or "",
                    due_at=item.next_action_at,
                )
                for item in summary.next_actions
                if item.next_action_at is not None
            ],
        )
    except (CommercialAuthorizationError, CommercialNotFoundError, CommercialRuleViolation) as exc:
        raise_commercial_error(exc)


@router.post("/discovery/import", response_model=DiscoveryJobResponse, status_code=201)
async def import_discovery(
    payload: DiscoveryImportRequest, discovery: Discovery
) -> DiscoveryJobResponse:
    try:
        records = [DiscoveryRecord(**item.model_dump()) for item in payload.records]
        outcome = await discovery.import_records(records, payload.provider)
        return DiscoveryJobResponse.model_validate(outcome.job, from_attributes=True)
    except (CommercialAuthorizationError, CommercialNotFoundError) as exc:
        raise_commercial_error(exc)


@router.get("/discovery/jobs", response_model=list[DiscoveryJobResponse])
async def discovery_jobs(discovery: Discovery) -> list[DiscoveryJobResponse]:
    try:
        return [
            DiscoveryJobResponse.model_validate(job, from_attributes=True)
            for job in await discovery.jobs()
        ]
    except (CommercialAuthorizationError, CommercialNotFoundError) as exc:
        raise_commercial_error(exc)


@router.post(
    "/companies/{company_id}/research", response_model=ResearchJobResponse, status_code=202
)
async def research_company(company_id: UUID, discovery: Discovery) -> ResearchJobResponse:
    try:
        job = await discovery.research(company_id)
        return ResearchJobResponse.model_validate(job, from_attributes=True)
    except (CommercialAuthorizationError, CommercialNotFoundError) as exc:
        raise_commercial_error(exc)


@router.get("/companies/{company_id}/evidence", response_model=EvidenceResponse)
async def company_evidence(company_id: UUID, discovery: Discovery) -> EvidenceResponse:
    try:
        analysis, signals = await discovery.evidence(company_id)
        return EvidenceResponse(
            observed=analysis.observed if analysis else {},
            hypotheses=analysis.hypotheses if analysis else {},
            signals=[SignalResponse.model_validate(item, from_attributes=True) for item in signals],
        )
    except (CommercialAuthorizationError, CommercialNotFoundError) as exc:
        raise_commercial_error(exc)
