# ADR-005 — Abstracción del proveedor de IA

Status: Accepted

Context: Varias capacidades futuras usarán IA, pero el dominio no debe depender de un proveedor ni delegarle decisiones críticas.

Decision: Toda IA se consumirá mediante interfaces propias. OpenAI será el proveedor inicial cuando llegue la fase correspondiente.

Alternatives: SDK del proveedor dentro del dominio; proveedor único sin abstracción.

Consequences: Sustitución y pruebas más sencillas a cambio de una capa adicional.

Security Impact: Minimización de datos, trazabilidad y revisión humana para resultados sensibles.

Migration Impact: Nuevos proveedores implementarán el mismo contrato de aplicación.

