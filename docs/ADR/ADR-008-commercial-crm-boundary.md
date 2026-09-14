# ADR-008 — CRM comercial como contexto independiente

Status: Accepted

Context: El control comercial debe gestionar prospección, cualificación y seguimiento sin depender del catálogo de servicios que ProcessOS ofrece a sus clientes. En fases posteriores incorporará fuentes de scraping.

Decision: El CRM vive en el contexto `commercial`, con modelos, casos de uso, permisos y API propios. Todas sus entidades contienen `organization_id`; este valor se obtiene de la identidad autenticada y nunca del cuerpo de una petición. Una oportunidad activa debe mantener `next_best_action` y `next_action_at`. El portal externo de auditoría no importa ni consume este contexto.

Alternatives: Reutilizar organizaciones cliente como leads; integrar el pipeline dentro del módulo de auditorías; adoptar un CRM externo como fuente primaria.

Consequences: El equipo puede evolucionar captación y scraping de forma autónoma. La conversión de una oportunidad ganada en cliente será un caso de uso explícito futuro, no una relación implícita entre tablas.

Security Impact: Los endpoints requieren `commercial.read` o `commercial.write`, aplican aislamiento por tenant en el repositorio y generan eventos de auditoría para mutaciones.

Migration Impact: Se crea el esquema `commercial_*` y se incorporan permisos comerciales a los roles existentes mediante Alembic.
