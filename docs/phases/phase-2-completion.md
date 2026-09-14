# Fase 2 — Commercial OS

Estado: Completada el 14 de septiembre de 2026.

## Resultado

El control comercial interno permite crear una empresa manualmente, asignarle la siguiente mejor acción, recorrer las etapas del pipeline hasta `won` o `lost`, registrar llamadas y consultar su historial en una ficha 360. `apps/web` permanece sin cambios y el CRM no depende de servicios contratados por clientes.

## Alcance entregado

- Contexto backend `commercial` separado por dominio, aplicación y persistencia.
- Entidades Company, Contact, Opportunity, Activity, Task, Call, Tag y Campaign.
- Pipeline tipado de 13 etapas y resultados de llamada tipados.
- Regla de dominio obligatoria para siguiente acción en oportunidades activas.
- API multi-tenant para cartera, detalle 360, cambio de etapa, llamadas y panel Hoy.
- Permisos `commercial.read` y `commercial.write`, con backfill para roles existentes.
- Panel Hoy, Kanban, tabla de empresas, cola de llamadas, alta manual y ficha Empresa 360.
- Eventos auditables para altas, cambios de etapa y llamadas.

## Evidencias

- `ruff`: correcto.
- `mypy --strict`: correcto.
- `pytest`: 11 pruebas superadas, incluidas reglas, aislamiento tenant y recorrido hasta ganada.
- `eslint`: correcto.
- `vitest`: 1 prueba superada.
- `next build`: correcto, incluidas rutas BFF y Empresa 360.
- Alembic/PostgreSQL: revisión `8bd1a42f937e (head)` aplicada correctamente.
- Smoke HTTP local: registro `201`, sesión BFF `200`, empresa `201`, panel Hoy `200`.

## Decisiones

La frontera del CRM y su preparación para futuras fuentes de scraping quedan recogidas en ADR-008. La automatización de scraping no forma parte de esta fase; se añadirá como adaptador de entrada sin convertir al CRM en una extensión de los servicios para clientes.
