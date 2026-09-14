# ADR-007 — Autenticación, sesiones y RBAC

Status: Accepted

Context: ProcessOS necesita autenticar usuarios en una organización concreta, revocar accesos y evitar que un identificador suministrado por frontend determine el tenant efectivo.

Decision: Las contraseñas se almacenan con Argon2. Un JWT breve identifica usuario, membresía, organización y sesión, pero cada petición comprueba también una sesión persistida no revocada y una membresía activa. Los roles pertenecen a una organización y la base de datos impide asignarlos a membresías de otra organización mediante una clave foránea compuesta. Los permisos se evalúan en backend.

Alternatives: JWT puramente stateless; rol incluido sin comprobación persistida; autorización solo en frontend.

Consequences: Logout y revocación son inmediatos. Cada petición autenticada requiere acceso a persistencia; podrá optimizarse con caché segura si las métricas lo justifican.

Security Impact: El secreto JWT es externo al repositorio y el valor de desarrollo se rechaza en producción. Los tokens son de corta duración, su versión persistida está hasheada y nunca se registra en logs.

Migration Impact: Cambios futuros de claims deberán mantener compatibilidad o invalidar sesiones explícitamente. MFA se añadirá sobre la sesión existente sin crear una identidad paralela.
