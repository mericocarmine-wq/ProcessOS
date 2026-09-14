# ADR-004 — Documentos privados

Status: Accepted

Context: ProcessOS manejará documentación financiera, fiscal y laboral sensible.

Decision: Los documentos usarán almacenamiento privado y acceso temporal firmado detrás de una interfaz de aplicación.

Alternatives: Objetos públicos; almacenamiento directo en la base de datos.

Consequences: Ninguna URL permanente pública. El proveedor concreto se elegirá en la Fase 6.

Security Impact: Validación de tipo y tamaño, aislamiento por tenant, hash, permisos y auditoría serán obligatorios.

Migration Impact: La abstracción permitirá cambiar de proveedor sin modificar el dominio.

