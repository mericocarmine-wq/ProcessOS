# Fase 1 — Evidencia de finalización

Status: Completed

## Alcance entregado

- Identidad: `Organization`, `User`, `Membership`, `Role` y `Permission`.
- Plataforma: `Application`, `Subscription`, `Integration`, `Notification`, `AuditEvent` y `FeatureFlag`.
- Autenticación: registro, login, JWT breve, sesión persistida revocable, logout y recuperación.
- MFA: identidad y modelo preparados mediante `mfa_enabled`; el enrolamiento pertenece al hardening posterior.
- RBAC: roles iniciales, permisos efectivos y autorización siempre en backend.
- Multi-tenancy: contexto de organización derivado de membresía autenticada y repositorios acotados.
- App Launcher: solo expone aplicaciones activas y habilitadas para la organización.
- Commercial App: sesión encapsulada por BFF con cookie `HttpOnly` y `SameSite=strict`.

## Evidencia automatizada

- Tests negativos impiden leer eventos de otra organización.
- Un token con organización distinta de su membresía es rechazado.
- Un usuario sin `apps.manage` no puede modificar aplicaciones.
- El último propietario no puede ser degradado.
- Un token de recuperación solo puede usarse una vez y revoca sesiones anteriores.
- Los endpoints de miembros, flags y audit log usan el tenant autenticado, nunca uno enviado por frontend.

## Validaciones de cierre

- Ruff: passed.
- mypy strict: passed.
- pytest: passed.
- ESLint: passed en ambos frontends.
- TypeScript strict: passed en ambos frontends.
- Vitest: passed en ambos frontends.
- Next.js production build: passed en ambos frontends.
- Alembic: PostgreSQL en `5a5bf2bdcaba (head)`.
- Health y readiness: HTTP 200.

## Riesgos aceptados para fases posteriores

- El enrolamiento MFA y step-up auth se completarán en Security Hardening.
- La entrega de recuperación requiere un proveedor SMTP configurado; los tokens nunca se registran.
- Invitaciones por correo se añadirán cuando exista un flujo de onboarding; Fase 1 permite añadir usuarios existentes.
