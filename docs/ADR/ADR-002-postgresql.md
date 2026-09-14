# ADR-002 — PostgreSQL

Status: Accepted

Context: Los dominios de ProcessOS requieren integridad referencial, transacciones, auditoría y consultas analíticas.

Decision: PostgreSQL será la base de datos relacional principal y SQLAlchemy la abstracción de persistencia del backend.

Alternatives: Bases documentales; múltiples bases de datos desde el inicio.

Consequences: Modelo consistente y transaccional; las migraciones se gestionan con Alembic.

Security Impact: Credenciales solo por configuración externa, usuario de mínimos privilegios y conexiones cifradas en producción.

Migration Impact: Los cambios de esquema requieren migraciones revisables y reversibles cuando sea viable.

