# Fase 4 — Discovery & Research

Estado: Completada el 14 de septiembre de 2026, antes de la Fase 3 por decisión recogida en ADR-009.

## Resultado

El CRM interno puede recibir campañas de empresas, normalizar y deduplicar registros, investigar sitios web públicos y transformar observaciones trazables en señales de cualificación. El proceso no crea clientes ni depende del futuro portal de auditorías.

## Alcance entregado

- Entidades DiscoveryJob, CompanySource, ResearchJob, WebsiteAnalysis, ReviewAnalysis y Signal.
- Importación de hasta 500 registros por job desde el adaptador CSV de la interfaz.
- Modelo de entrada independiente para añadir futuras fuentes públicas permitidas.
- Deduplicación por dominio, teléfono, nombre + ciudad y `provider + external_id`.
- Research web de home con detección de contacto, booking, portal, blog, formulario, WhatsApp, chat, CTA y pistas tecnológicas.
- Evidencia observada e hipótesis almacenadas y presentadas por separado.
- Scoring inicial y movimiento automático a `researched` después de un análisis correcto.
- Timeout, respuesta máxima de 1 MB, un reintento, bloqueo de direcciones privadas/reservadas, HTTP(S) obligatorio y redirecciones deshabilitadas.
- Fallos de investigación aislados en su propio ResearchJob mediante códigos seguros.
- Trazabilidad de importaciones, fuentes, research, señales y eventos de auditoría.
- Vista Discovery, historial de jobs, importación CSV e investigación desde Empresa 360.

## Evidencias

- `ruff`: correcto.
- `mypy --strict`: correcto.
- `pytest`: 14 pruebas superadas.
- `eslint`: correcto.
- `vitest`: 1 prueba superada.
- `next build`: correcto.
- Alembic/PostgreSQL: revisión `c91f4e72a630 (head)` aplicada y sin diferencias de esquema.
- Smoke HTTP: login `200`; primera importación creó 1 empresa; segunda importación normalizada creó 0 y detectó 1 duplicada.

## Pendiente deliberado

Los conectores de directorios, buscadores, OpenStreetMap y fuentes sectoriales se incorporarán como adaptadores adicionales cuando se definan proveedor, condiciones de uso y límites operativos. El envío de auditorías permanece manual hasta completar la Fase 3.
