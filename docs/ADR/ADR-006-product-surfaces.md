# ADR-006 — Superficies de producto separadas

Status: Accepted

Context: ProcessOS necesita una herramienta comercial interna y un entorno externo de auditoría. Los servicios operativos contratados por clientes son un tercer contexto y no deben contaminar el CRM.

Decision: `apps/app` será el control comercial interno y `apps/web` el portal público de auditorías. Compartirán API mediante contratos explícitos, pero tendrán navegación, autenticación, permisos y ciclos de despliegue independientes. La conversión de prospecto a organización cliente será un caso de uso explícito y auditable.

Alternatives: Una única aplicación con rutas mezcladas; duplicar backend y datos.

Consequences: Límites de seguridad y producto más claros a cambio de operar dos frontends.

Security Impact: El portal externo no heredará permisos internos. Un token de auditoría nunca concederá acceso al CRM ni a módulos contratados.

Migration Impact: Docker, CI y documentación deberán validar ambos frontends. Los módulos comerciales y de cliente conservarán modelos separados.
