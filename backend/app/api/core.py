from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import CurrentIdentity
from app.api.health import get_session
from app.core.application.apps import (
    AppLauncherService,
    ApplicationNotFoundError,
    AuthorizationError,
    CoreApplicationError,
)
from app.core.application.management import (
    CoreManagementService,
    ManagementConflictError,
    ManagementNotFoundError,
)
from app.core.domain.context import OrganizationContext
from app.core.domain.enums import MembershipRole
from app.core.persistence.app_repository import SqlAlchemyAppRepository
from app.core.persistence.management_repository import SqlAlchemyManagementRepository

router = APIRouter(prefix="/core", tags=["core"])
Session = Annotated[AsyncSession, Depends(get_session)]


class ApplicationResponse(BaseModel):
    code: str
    name: str


class ApplicationStateRequest(BaseModel):
    enabled: bool


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    email: str
    role: str
    active: bool


class AddMemberRequest(BaseModel):
    email: EmailStr
    role: MembershipRole


class ChangeRoleRequest(BaseModel):
    role: MembershipRole


class FeatureFlagResponse(BaseModel):
    key: str
    enabled: bool


class FeatureFlagRequest(BaseModel):
    enabled: bool


class AuditEventResponse(BaseModel):
    action: str
    resource_type: str
    resource_id: str | None
    result: str
    created_at: datetime


def build_app_launcher(session: Session, identity: CurrentIdentity) -> AppLauncherService:
    context = OrganizationContext(
        organization_id=identity.organization_id,
        actor_id=identity.user_id,
    )
    return AppLauncherService(SqlAlchemyAppRepository(session, context), identity)


AppLauncher = Annotated[AppLauncherService, Depends(build_app_launcher)]


def build_management(session: Session, identity: CurrentIdentity) -> CoreManagementService:
    context = OrganizationContext(identity.organization_id, identity.user_id)
    return CoreManagementService(SqlAlchemyManagementRepository(session, context), identity)


Management = Annotated[CoreManagementService, Depends(build_management)]


@router.get("/apps", response_model=list[ApplicationResponse])
async def list_enabled_apps(launcher: AppLauncher) -> list[ApplicationResponse]:
    try:
        apps = await launcher.list_enabled()
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [ApplicationResponse(code=app.code, name=app.name) for app in apps]


@router.put("/apps/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def set_app_state(
    code: str,
    payload: ApplicationStateRequest,
    launcher: AppLauncher,
) -> None:
    try:
        await launcher.set_enabled(code, payload.enabled)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CoreApplicationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/roles", response_model=list[str])
async def list_roles(identity: CurrentIdentity) -> list[str]:
    if "members.read" not in identity.permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing permission")
    return [role.value for role in MembershipRole]


@router.get("/members", response_model=list[MemberResponse])
async def list_members(management: Management) -> list[MemberResponse]:
    try:
        members = await management.list_members()
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [MemberResponse.model_validate(member) for member in members]


@router.post("/members", status_code=status.HTTP_201_CREATED)
async def add_member(payload: AddMemberRequest, management: Management) -> None:
    try:
        await management.add_member(str(payload.email).lower(), payload.role.value)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ManagementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ManagementConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/members/{membership_id}/role", status_code=status.HTTP_204_NO_CONTENT)
async def change_member_role(
    membership_id: UUID,
    payload: ChangeRoleRequest,
    management: Management,
) -> None:
    try:
        await management.change_member_role(membership_id, payload.role.value)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ManagementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ManagementConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/feature-flags", response_model=list[FeatureFlagResponse])
async def list_feature_flags(management: Management) -> list[FeatureFlagResponse]:
    try:
        flags = await management.list_flags()
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [FeatureFlagResponse(key=flag.key, enabled=flag.enabled) for flag in flags]


@router.put("/feature-flags/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def set_feature_flag(
    key: Annotated[str, Field(pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$", max_length=100)],
    payload: FeatureFlagRequest,
    management: Management,
) -> None:
    try:
        await management.set_flag(key, payload.enabled)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/audit-events", response_model=list[AuditEventResponse])
async def list_audit_events(management: Management) -> list[AuditEventResponse]:
    try:
        events = await management.list_audit_events()
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [
        AuditEventResponse(
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            result=event.result,
            created_at=event.created_at,
        )
        for event in events
    ]
