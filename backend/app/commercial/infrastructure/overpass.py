import asyncio
import logging
import math
import time
from collections import OrderedDict
from dataclasses import dataclass

import httpx

from app.commercial.domain.discovery import DiscoveryRecord

DEFAULT_OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
MAX_RESULTS = 100
logger = logging.getLogger(__name__)
# Public source data only; never cache organization records or credentials.
_cache: OrderedDict[tuple[tuple[str, ...], str], tuple[float, dict[str, object]]] = OrderedDict()

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
    timeout_seconds: float = 12.0
    total_timeout_seconds: float = 35.0
    endpoints: tuple[str, ...] = DEFAULT_OVERPASS_ENDPOINTS

    @property
    def code(self) -> str:
        return "openstreetmap"

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _query(self, sector: str, latitude: float, longitude: float, limit: int) -> str:
        filters = SECTOR_FILTERS.get(sector)
        if filters is None:
            raise ValueError("Unsupported sector")
        # A 10 x 10 km viewport, not an expensive global administrative-area lookup.
        delta_lat = 5 / 111.32
        delta_lon = 5 / (111.32 * math.cos(math.radians(latitude)))
        bounds = (
            f"{latitude - delta_lat:.6f},{longitude - delta_lon:.6f},"
            f"{latitude + delta_lat:.6f},{longitude + delta_lon:.6f}"
        )
        selectors = "\n".join(
            f'nwr["{key}"="{value}"]["name"]({bounds});' for key, value in filters
        )
        return f"[out:json][timeout:8];({selectors});out tags center {min(limit, MAX_RESULTS)};"

    async def _locate(self, city: str) -> tuple[float, float]:
        parts = city.strip().split(",")
        if len(parts) == 2:
            try:
                latitude, longitude = map(float, parts)
            except ValueError as exc:
                raise ValueError("Introduce un nombre de localidad o latitud,longitud.") from exc
            if not (-85 <= latitude <= 85 and -179 <= longitude <= 179):
                raise ValueError("Coordenadas fuera del rango admitido.")
            return latitude, longitude
        query = (
            '[out:json][timeout:8];node["place"~"^(city|town|village)$"]'
            f'["name"="{self._escape(city.strip())}"];out body 100;'
        )
        payload = await self._fetch(query)
        elements = payload["elements"]
        assert isinstance(elements, list)
        # Prefer cities over towns/villages; do not arbitrarily choose equal-rank homonyms.
        for kind in ("city", "town", "village"):
            matches = [
                e
                for e in elements
                if isinstance(e, dict)
                and isinstance(e.get("tags"), dict)
                and e["tags"].get("place") == kind
            ]
            if len(matches) > 1 or len(elements) >= 100:
                raise ValueError("Hay varias localidades con ese nombre. Usa latitud,longitud.")
            if matches:
                try:
                    latitude, longitude = float(matches[0]["lat"]), float(matches[0]["lon"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise DiscoveryProviderError(
                        "Invalid location coordinates from source"
                    ) from exc
                if not (-85 <= latitude <= 85 and -179 <= longitude <= 179):
                    raise ValueError("Localidad fuera del rango geográfico admitido.")
                return latitude, longitude
        raise ValueError("No se encontró la localidad. Revisa el nombre o usa latitud,longitud.")

    async def _fetch(self, query: str) -> dict[str, object]:
        key = (self.endpoints, query)
        cached = _cache.get(key)
        if cached and cached[0] > time.monotonic():
            _cache.move_to_end(key)
            return cached[1]
        last_error: Exception | None = None
        for endpoint in self.endpoints:
            try:
                payload = await self._fetch_endpoint(endpoint, query)
                _cache[key] = (time.monotonic() + 600, payload)
                _cache.move_to_end(key)
                while len(_cache) > 128:
                    _cache.popitem(last=False)
                return payload
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                last_error = exc
                logger.warning(
                    "discovery_provider_failed endpoint=%s error=%s status=%s",
                    endpoint,
                    type(exc).__name__,
                    exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None,
                )
        raise DiscoveryProviderError("OpenStreetMap discovery failed") from last_error

    async def _fetch_endpoint(self, endpoint: str, query: str) -> dict[str, object]:
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            headers={"User-Agent": "ProcessOS/1.0"},
        ) as client:
            response = await client.get(endpoint, params={"data": query})
            response.raise_for_status()
            payload: dict[str, object] = response.json()
            if not isinstance(payload, dict) or payload.get("remark"):
                raise ValueError("Overpass returned an incomplete or failed query")
            if not isinstance(payload.get("elements"), list):
                raise ValueError("Invalid Overpass response")
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
        if sector not in SECTOR_FILTERS or not 1 <= limit <= MAX_RESULTS:
            raise ValueError("Sector o límite de resultados no válido.")
        try:
            async with asyncio.timeout(self.total_timeout_seconds):
                latitude, longitude = await self._locate(city)
                payload = await self._fetch(self._query(sector, latitude, longitude, limit))
                return self._records(payload, city, limit)
        except TimeoutError as exc:
            raise DiscoveryProviderError("Discovery time budget exceeded") from exc
