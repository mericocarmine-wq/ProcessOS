import asyncio
from dataclasses import dataclass

import httpx

from app.commercial.domain.discovery import DiscoveryRecord

DEFAULT_OVERPASS_ENDPOINTS = (
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
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

    async def _fetch_endpoint(self, endpoint: str, query: str) -> dict[str, object]:
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            headers={"User-Agent": "ProcessOS-Commercial/1.0 (internal discovery)"},
        ) as client:
            response = await client.get(endpoint, params={"data": query})
            response.raise_for_status()
            payload: dict[str, object] = response.json()
            return payload

    @staticmethod
    def _records(payload: dict[str, object], city: str, limit: int) -> list[DiscoveryRecord]:
        elements = payload.get("elements", [])
        if not isinstance(elements, list):
            raise ValueError("Invalid Overpass response")
        records = []
        for element in elements[:limit]:
            if not isinstance(element, dict):
                continue
            tags = element.get("tags", {})
            if not isinstance(tags, dict):
                continue
            name = str(tags.get("name", "")).strip()
            if not name:
                continue
            element_type = str(element.get("type", "node"))
            element_id = str(element.get("id", ""))
            records.append(
                DiscoveryRecord(
                    name=name,
                    domain=tags.get("website") or tags.get("contact:website"),
                    phone=tags.get("phone") or tags.get("contact:phone"),
                    city=tags.get("addr:city") or city,
                    email=tags.get("email") or tags.get("contact:email"),
                    external_id=f"{element_type}/{element_id}",
                    source_url=f"https://www.openstreetmap.org/{element_type}/{element_id}",
                )
            )
        return records

    async def search(self, sector: str, city: str, limit: int) -> list[DiscoveryRecord]:
        query = self._query(sector, city, limit)
        last_error: Exception | None = None
        tasks = [
            asyncio.create_task(self._fetch_endpoint(endpoint, query))
            for endpoint in self.endpoints
        ]
        try:
            for completed in asyncio.as_completed(tasks, timeout=self.timeout_seconds + 1):
                try:
                    return self._records(await completed, city, limit)
                except (httpx.HTTPError, ValueError, KeyError) as exc:
                    last_error = exc
        except TimeoutError as exc:
            last_error = exc
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        raise DiscoveryProviderError("OpenStreetMap discovery failed") from last_error
