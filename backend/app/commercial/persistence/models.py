from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.persistence.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_companies"
    __table_args__ = (
        UniqueConstraint("organization_id", "domain", name="uq_commercial_company_org_domain"),
        Index("ix_commercial_company_org_name", "organization_id", "name"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(320))
    city: Mapped[str | None] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    qualification_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    opportunity: Mapped["Opportunity"] = relationship(back_populates="company", lazy="selectin")
    contacts: Mapped[list["Contact"]] = relationship(back_populates="company", lazy="selectin")


class Opportunity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_opportunities"
    __table_args__ = (Index("ix_commercial_opportunity_org_stage", "organization_id", "stage"),)

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("commercial_companies.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    stage: Mapped[str] = mapped_column(String(30), default="discovered", nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(12, 2))
    next_best_action: Mapped[str | None] = mapped_column(String(255))
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    company: Mapped[Company] = relationship(back_populates="opportunity")


class Contact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_contacts"
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("commercial_companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    company: Mapped[Company] = relationship(back_populates="contacts")


class Activity(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "commercial_activities"
    __table_args__ = (Index("ix_commercial_activity_org_company", "organization_id", "company_id"),)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("commercial_companies.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("core_users.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Call(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "commercial_calls"
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("commercial_companies.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("core_users.id", ondelete="SET NULL"))
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_tasks"
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("commercial_companies.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_tags"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_campaigns"
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
