import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class DiscoveryRecord:
    name: str
    domain: str | None = None
    phone: str | None = None
    city: str | None = None
    email: str | None = None
    external_id: str | None = None
    source_url: str | None = None


def normalize_domain(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip().lower()
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    hostname = parsed.hostname
    return hostname.removeprefix("www.") if hostname else None


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    normalized = "".join(
        character for character in value if character.isdigit() or character == "+"
    )
    return normalized or None


def normalize_name(value: str) -> str:
    return " ".join(value.lower().strip().split())


def is_public_address(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )
