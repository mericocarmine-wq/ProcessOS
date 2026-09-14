from collections.abc import Sequence


def normalize_allowed_origins(origins: Sequence[object]) -> list[str]:
    """Convert validated URLs to the exact strings expected by CORS middleware."""

    return [str(origin).rstrip("/") for origin in origins]

