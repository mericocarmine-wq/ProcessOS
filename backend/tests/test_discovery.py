from uuid import uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.commercial.application.discovery import DiscoveryService
from app.commercial.domain.discovery import DiscoveryRecord, is_public_address, normalize_domain
from app.commercial.domain.research import FetchedPage, analyze_website
from app.commercial.persistence.repository import SqlAlchemyCommercialRepository
from app.core.application.auth import AuthenticatedIdentity
from app.core.domain.context import OrganizationContext
from app.core.persistence.base import Base
from app.core.persistence.models import Organization, User


class FakeFetcher:
    async def fetch(self, url: str) -> FetchedPage:
        return FetchedPage(
            url,
            "<html><title>Acme</title><form></form><a href='https://wa.me/1'>WhatsApp</a></html>",
        )


def test_normalization_and_ssrf_rules() -> None:
    assert normalize_domain("https://WWW.Example.com/path") == "example.com"
    assert not is_public_address("127.0.0.1")
    assert not is_public_address("10.0.0.4")
    assert is_public_address("93.184.216.34")


def test_research_separates_observation_from_hypothesis() -> None:
    result = analyze_website("<title>Example</title><form>Contacta</form>")
    assert result.observed["has_form"] is True
    assert result.hypotheses["automation_opportunity"]
    assert all(signal[1] in {"detected", "not_detected"} for signal in result.signals)


async def test_discovery_deduplicates_and_researches_without_external_provider() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        organization = Organization(name="Discovery", slug="discovery")
        actor = User(email="discovery@example.com", password_hash=uuid4().hex)
        session.add_all([organization, actor])
        await session.flush()
        identity = AuthenticatedIdentity(
            actor.id,
            actor.email,
            organization.id,
            organization.name,
            uuid4(),
            "owner",
            frozenset({"commercial.read", "commercial.write"}),
            uuid4(),
        )
        service = DiscoveryService(
            SqlAlchemyCommercialRepository(session, OrganizationContext(organization.id, actor.id)),
            identity,
            FakeFetcher(),
        )
        outcome = await service.import_records(
            [
                DiscoveryRecord("Acme", "www.acme.example", city="Madrid"),
                DiscoveryRecord("ACME", "https://acme.example", city="Madrid"),
            ]
        )
        job = await service.research(outcome.companies[0].id)
        analysis, signals = await service.evidence(outcome.companies[0].id)
    assert outcome.job.created_count == 1
    assert outcome.job.duplicate_count == 1
    assert job.status == "completed"
    assert analysis and analysis.observed["has_whatsapp"] is True
    assert signals and all(signal.evidence_type == "observed" for signal in signals)
    await engine.dispose()
