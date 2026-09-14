# ADR-003 — Multi-tenancy por organización

Status: Accepted

Context: Una instancia sirve a varias organizaciones y el aislamiento es un requisito crítico.

Decision: Toda entidad empresarial incluirá `organization_id`. La organización efectiva se resolverá desde la identidad autenticada; nunca desde un identificador aportado por el cliente como autoridad.

Alternatives: Base por tenant; esquema por tenant.

Consequences: Operación sencilla y consultas obligatoriamente acotadas. La Fase 1 añadirá tests negativos de aislamiento y evaluará defensa en profundidad con RLS.

Security Impact: Una consulta sin ámbito de organización se considera vulnerabilidad crítica.

Migration Impact: Todas las tablas empresariales futuras necesitarán clave foránea e índice de organización.

