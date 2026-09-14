# ProcessOS

Business Operating System modular y multi-tenant para autónomos y pymes.

El repositorio se encuentra en la **Fase 0 — Foundation & Security Baseline**. No contiene todavía lógica de negocio.

## Requisitos

- Docker 29+
- Docker Compose 2+

## Inicio rápido

```bash
cp .env.example .env
docker compose up --build
```

Servicios:

- Auditorías externas: <http://localhost:3000>
- Commercial OS interno: <http://localhost:3001>
- API: <http://localhost:8000>
- Health: <http://localhost:8000/health>
- Readiness: <http://localhost:8000/ready>

## Validación

```bash
docker compose run --rm backend pytest
docker compose run --rm backend ruff check .
docker compose run --rm backend mypy app tests
docker compose run --rm web npm run check
docker compose run --rm app npm run check
```

## Arquitectura

ProcessOS comienza como monolito modular. El dominio no depende de FastAPI, SQLAlchemy, proveedores de IA ni herramientas de automatización. Las decisiones relevantes se registran en [`docs/ADR`](docs/ADR).

Consulta [`PROCESSOS-fases.md`](PROCESSOS-fases.md) para el plan completo.
