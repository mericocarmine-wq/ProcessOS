from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.persistence.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

role_permissions = Table(
    "core_role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("core_roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id", ForeignKey("core_permissions.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_roles"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_core_roles_org_name"),
        UniqueConstraint("organization_id", "id", name="uq_core_roles_org_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, lazy="selectin"
    )


class Permission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "core_permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)


class Membership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id"),
        ForeignKeyConstraint(
            ["organization_id", "role_id"],
            ["core_roles.organization_id", "core_roles.id"],
            ondelete="RESTRICT",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role_id: Mapped[UUID] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[Role] = relationship(lazy="joined")


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_apps"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Subscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_subscriptions"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)


class OrganizationApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_organization_apps"
    __table_args__ = (UniqueConstraint("organization_id", "app_id"),)

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    app_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_apps.id", ondelete="CASCADE"), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Integration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_integrations"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    safe_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_notifications"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("core_users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "core_audit_events"
    __table_args__ = (
        Index("ix_core_audit_events_org_created", "organization_id", "created_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("core_users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100))
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    safe_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FeatureFlag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_feature_flags"
    __table_args__ = (UniqueConstraint("organization_id", "key"),)

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AuthSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "core_auth_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PasswordResetToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "core_password_reset_tokens"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
