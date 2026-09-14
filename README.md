# ProcessOS

Business Operating System modular y multi-tenant para autónomos y pymes.

El repositorio se encuentra en la **Fase 1 — ProcessOS Core**. Incluye identidad, sesiones,
organizaciones, RBAC, aislamiento multi-tenant y App Launcher; todavía no contiene lógica de los
dominios comerciales o de servicio.

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
- API docs (solo no producción): <http://localhost:8000/docs>

## Superficies de producto

- `apps/app`: control comercial interno e independiente.
- `apps/web`: portal externo para auditorías empresariales.
- `backend`: API modular compartida con límites de autorización propios.

## API Core

- `POST /auth/register`: crea usuario propietario y organización.
- `POST /auth/login`: emite una sesión revocable acotada a una membresía.
- `GET /auth/me`: devuelve identidad, organización, rol y permisos efectivos.
- `POST /auth/logout`: revoca la sesión actual.
- `GET /core/apps`: devuelve únicamente las aplicaciones habilitadas.
- `PUT /core/apps/{code}`: modifica una aplicación si existe `apps.manage`.

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
