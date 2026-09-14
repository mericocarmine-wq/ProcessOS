from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import CurrentIdentity
from app.api.health import get_session
from app.core.application.apps import (
    AppLauncherService,
    ApplicationNotFoundError,
    AuthorizationError,
    CoreApplicationError,
)
from app.core.domain.context import OrganizationContext
from app.core.persistence.app_repository import SqlAlchemyAppRepository

router = APIRouter(prefix="/core", tags=["core"])
Session = Annotated[AsyncSession, Depends(get_session)]


class ApplicationResponse(BaseModel):
    code: str
    name: str


class ApplicationStateRequest(BaseModel):
    enabled: bool


def build_app_launcher(session: Session, identity: CurrentIdentity) -> AppLauncherService:
    context = OrganizationContext(
        organization_id=identity.organization_id,
        actor_id=identity.user_id,
    )
    return AppLauncherService(SqlAlchemyAppRepository(session, context), identity)


AppLauncher = Annotated[AppLauncherService, Depends(build_app_launcher)]


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
