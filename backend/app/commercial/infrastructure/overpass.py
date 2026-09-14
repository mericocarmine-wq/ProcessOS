import asyncio
from dataclasses import dataclass

import httpx

from app.commercial.domain.discovery import DiscoveryRecord

DEFAULT_OVERPASS_ENDPOINTS = (
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
)
MAX_RESULTS = 100

SECTOR_FILTERS: dict[str, tuple[tuple[str, str], ...]] = {
    "accounting": (("office", "accountant"), ("office", "tax_advisor")),
    "car_repair": (("shop", "car_repair"),),
    "clinic": (("amenity", "clinic"), ("amenity", "doctors"), ("amenity", "dentist")),
    "construction": (("office", "construction_company"), ("craft", "builder")),
    "hairdresser": (("shop", "hairdresser"),),
    "hotel": (("tourism", "hotel"), ("tourism", "guest_house")),
    "law": (("office", "lawyer"),),
    "real_estate": (("office", "estate_agent"),),
    "restaurant": (("amenity", "restaurant"), ("amenity", "cafe")),
}


class DiscoveryProviderError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OverpassDiscoveryProvider:
    timeout_seconds: float = 18.0
    endpoints: tuple[str, ...] = DEFAULT_OVERPASS_ENDPOINTS

    @property
    def code(self) -> str:
        return "openstreetmap"

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _query(self, sector: str, city: str, limit: int) -> str:
        filters = SECTOR_FILTERS.get(sector)
        if filters is None:
            raise ValueError("Unsupported sector")
        area = self._escape(city.strip())
        selectors = "\n".join(
            f'nwr["{key}"="{value}"]["name"](area.searchArea);' for key, value in filters
        )
        return (
            f'[out:json][timeout:20];area["name"="{area}"]'
            '["boundary"="administrative"]["admin_level"="8"]->.searchArea;('
            f"{selectors});out tags center {min(limit, MAX_RESULTS)};"
        )

    async def search(self, sector: str, city: str, limit: int) -> list[DiscoveryRecord]:
        query = self._query(sector, city, limit)
        last_error: Exception | None = None
        for index, endpoint in enumerate(self.endpoints):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds,
                    headers={"User-Agent": "ProcessOS-Commercial/1.0 (internal discovery)"},
                ) as client:
                    response = await client.get(endpoint, params={"data": query})
                    response.raise_for_status()
                    payload = response.json()
                records = []
                for element in payload.get("elements", [])[:limit]:
                    tags = element.get("tags", {})
                    records.append(
                        DiscoveryRecord(
                            name=tags.get("name", "").strip(),
                            domain=tags.get("website") or tags.get("contact:website"),
                            phone=tags.get("phone") or tags.get("contact:phone"),
                            city=tags.get("addr:city") or city,
                            email=tags.get("email") or tags.get("contact:email"),
                            external_id=f"{element.get('type')}/{element.get('id')}",
                            source_url=(
                                f"https://www.openstreetmap.org/{element.get('type')}/"
                                f"{element.get('id')}"
                            ),
                        )
                    )
                return [record for record in records if record.name]
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                last_error = exc
                if index < len(self.endpoints) - 1:
                    await asyncio.sleep(0.5)
        raise DiscoveryProviderError("OpenStreetMap discovery failed") from last_error
