from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.health import get_session
from app.core.application.auth import (
    AccountConflictError,
    AuthenticatedIdentity,
    AuthenticationError,
    AuthService,
    InvalidRecoveryTokenError,
    RecoveryUnavailableError,
)
from app.core.email import SmtpPasswordResetDelivery
from app.core.persistence.auth_repository import SqlAlchemyAuthRepository
from app.core.security import TokenService

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    organization_name: str = Field(min_length=2, max_length=200)
    organization_slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)


class RegisterResponse(BaseModel):
    user_id: UUID
    organization_id: UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    organization_slug: str = Field(min_length=1, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth token scheme, not a credential
    expires_at: str


class IdentityResponse(BaseModel):
    user_id: UUID
    email: str
    organization_id: UUID
    organization_name: str
    role: str
    permissions: list[str]


class PasswordRecoveryRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=12, max_length=128)


Session = Annotated[AsyncSession, Depends(get_session)]


def build_auth_service(session: Session, request: Request) -> AuthService:
    settings = request.app.state.settings
    delivery = None
    if all(
        [settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]
    ):
        delivery = SmtpPasswordResetDelivery(settings)
    return AuthService(
        SqlAlchemyAuthRepository(session),
        TokenService(settings),
        recovery_delivery=delivery,
        password_reset_minutes=settings.password_reset_minutes,
        password_reset_base_url=str(settings.password_reset_base_url),
    )


Auth = Annotated[AuthService, Depends(build_auth_service)]


async def current_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    auth: Auth,
) -> AuthenticatedIdentity:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    try:
        return await auth.authenticate(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


CurrentIdentity = Annotated[AuthenticatedIdentity, Depends(current_identity)]


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, auth: Auth) -> RegisterResponse:
    try:
        user, organization = await auth.register_owner(
            email=str(payload.email).lower(),
            password=payload.password,
            organization_name=payload.organization_name,
            organization_slug=payload.organization_slug,
        )
    except AccountConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return RegisterResponse(user_id=user.id, organization_id=organization.id)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, auth: Auth) -> TokenResponse:
    try:
        issued = await auth.login(
            email=str(payload.email).lower(),
            password=payload.password,
            organization_slug=payload.organization_slug,
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(
        access_token=issued.access_token,
        expires_at=issued.expires_at.isoformat(),
    )


@router.get("/me", response_model=IdentityResponse)
async def me(identity: CurrentIdentity) -> IdentityResponse:
    return IdentityResponse(
        user_id=identity.user_id,
        email=identity.email,
        organization_id=identity.organization_id,
        organization_name=identity.organization_name,
        role=identity.role,
        permissions=sorted(identity.permissions),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(identity: CurrentIdentity, auth: Auth) -> None:
    await auth.logout(identity)


@router.post("/password-recovery", status_code=status.HTTP_202_ACCEPTED)
async def request_password_recovery(payload: PasswordRecoveryRequest, auth: Auth) -> None:
    try:
        await auth.request_password_reset(str(payload.email).lower())
    except RecoveryUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post("/password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(payload: PasswordResetRequest, auth: Auth) -> None:
    try:
        await auth.reset_password(payload.token, payload.new_password)
    except InvalidRecoveryTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
