# ADR-001 — Monolito modular

Status: Accepted

Context: ProcessOS abarcará varios dominios, pero el equipo necesita velocidad operativa sin asumir prematuramente el coste distribuido.

Decision: Backend único desplegable, organizado por módulos de dominio con límites explícitos. Las integraciones entre módulos se harán mediante interfaces y eventos internos.

Alternatives: Microservicios desde el inicio; aplicación monolítica sin límites modulares.

Consequences: Operación y transacciones simples; exige disciplina para impedir acoplamiento entre módulos.

Security Impact: Un único perímetro inicial facilita políticas consistentes, sin sustituir controles por módulo.

Migration Impact: Un módulo podrá extraerse si métricas y necesidades operativas justifican el coste.

