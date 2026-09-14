import re
from dataclasses import dataclass
from html import unescape


@dataclass(frozen=True, slots=True)
class ResearchResult:
    title: str | None
    observed: dict[str, object]
    hypotheses: dict[str, object]
    signals: tuple[tuple[str, str, int], ...]


@dataclass(frozen=True, slots=True)
class FetchedPage:
    url: str
    content: str


_FEATURES = {
    "has_contact": ("contacto", "contact us", "mailto:"),
    "has_booking": ("reservar", "booking", "calendly"),
    "has_portal": ("área de cliente", "client area", "login"),
    "has_blog": ("/blog", "noticias"),
    "has_form": ("<form",),
    "has_whatsapp": ("whatsapp", "wa.me"),
    "has_chat": ("intercom", "crisp.chat", "livechat"),
    "has_cta": ("solicita", "contacta", "pide presupuesto", "request a quote"),
}


def analyze_website(html: str) -> ResearchResult:
    lowered = html.lower()
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = unescape(re.sub(r"\s+", " ", title_match.group(1)).strip()) if title_match else None
    observed: dict[str, object] = {
        key: any(term in lowered for term in terms) for key, terms in _FEATURES.items()
    }
    observed["technology_hints"] = [
        technology
        for technology in ("wordpress", "shopify", "hubspot", "react", "next.js")
        if technology in lowered
    ]
    hypotheses: dict[str, object] = {}
    if observed["has_form"] and not observed["has_chat"]:
        hypotheses["automation_opportunity"] = "Lead intake may rely on manual form handling"
    signals = tuple(
        (key, "detected" if present else "not_detected", 95)
        for key, present in observed.items()
        if isinstance(present, bool)
    )
    return ResearchResult(title, observed, hypotheses, signals)
