# ADR-009 — Adelantar Discovery & Research

Status: Accepted

Context: La captación y cualificación del CRM aporta valor antes de disponer del portal externo de auditorías. El orden maestro situaba Audit antes de Discovery & Research.

Decision: Ejecutar la Fase 4 después de Commercial OS y antes de Audit. Discovery entra al CRM mediante registros normalizados y fuentes identificadas. Research opera como jobs aislados y produce evidencia observada e hipótesis separadas. Ningún job crea clientes ni envía auditorías.

Alternatives: Mantener el orden original; implementar temporalmente una auditoría simulada; acoplar scraping a la futura aplicación externa.

Consequences: El CRM puede utilizarse para captación inmediatamente. La acción `audit_sent` seguirá siendo manual hasta implementar la Fase 3.

Security Impact: Las URLs se validan contra SSRF, solo aceptan HTTP(S) público, no siguen redirecciones, tienen timeout, límite de respuesta y reintentos acotados.

Migration Impact: Se añaden jobs, fuentes, análisis y señales bajo tablas `commercial_*`; no se modifica el esquema de Audit.
