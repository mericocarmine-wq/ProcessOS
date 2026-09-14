PROCESSOS — AI DEVELOPMENT MASTER BY PHASES

Documento maestro para desarrollar ProcessOS con IA en VS Code / Codex

Versión: 1.0
Estado: Documento de ejecución técnica por fases
Objetivo: Construir ProcessOS de forma incremental, modular, segura y mantenible utilizando IA como copiloto de desarrollo.

0. CÓMO USAR ESTE DOCUMENTO

Este archivo debe permanecer en el repositorio y utilizarse como contexto maestro para cualquier IA que participe en el desarrollo.

La IA debe:

Leer este documento.

Identificar la fase activa.

No adelantarse a fases futuras salvo necesidad arquitectónica real.

Mantener compatibilidad con lo ya construido.

Crear código pequeño, testeable y documentado.

Ejecutar validaciones antes de considerar una tarea terminada.

No modificar módulos no relacionados sin necesidad.

No romper seguridad, aislamiento multi-tenant ni contratos existentes.

Documentar decisiones arquitectónicas importantes.

No desplegar automáticamente a producción.

1. PRINCIPIOS NO NEGOCIABLES

Seguridad

VELOCIDAD
nunca
>
SEGURIDAD

Arquitectura

Modular Monolith primero
Microservicios solo cuando exista una necesidad real

Multi-tenant

Toda entidad empresarial debe pertenecer a:

organization_id

IA

La IA puede interpretar, clasificar, resumir, detectar anomalías, sugerir y explicar.

La IA no debe ser la única responsable de:

cálculos fiscales;

nóminas;

permisos;

acciones administrativas críticas;

representación oficial;

decisiones jurídicas.

Regla de dominio

domain
NO depende de
FastAPI
SQLAlchemy
Supabase
OpenAI
n8n

2. STACK OFICIAL

Frontend

Next.js
React
TypeScript
Tailwind CSS
shadcn/ui

Backend

Python
FastAPI
Pydantic
SQLAlchemy
Alembic

Base de datos

PostgreSQL

Calidad

Backend:

ruff
mypy
pytest
pytest-asyncio
httpx

Frontend:

eslint
prettier
typescript strict
vitest
React Testing Library
Playwright E2E

Infraestructura

Docker
Docker Compose
GitHub
GitHub Actions
Vercel

IA

Provider abstraction
OpenAI inicialmente

Automatización

n8n Community

3. ESTRUCTURA DE REPOSITORIO OBJETIVO

processos/
│
├── apps/
│   ├── web/
│   └── admin/
│
├── backend/
│   └── app/
│       ├── core/
│       ├── crm/
│       ├── audit/
│       ├── finance/
│       ├── tax/
│       ├── docs/
│       ├── hr/
│       ├── payroll/
│       ├── time/
│       ├── compliance/
│       ├── integrations/
│       └── shared/
│
├── automation/
│   └── n8n/
│
├── docs/
│   ├── ADR/
│   ├── architecture/
│   ├── security/
│   └── api/
│
├── tests/
├── scripts/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

FASE 0 — FOUNDATION & SECURITY BASELINE

Objetivo

Crear una base profesional, segura y estable.

Construir

repositorio;

FastAPI;

Next.js;

Docker;

PostgreSQL;

configuración;

logging;

health checks;

linting;

typing;

testing;

CI básico.

Backend inicial

backend/app/main.py
backend/app/core/config.py
backend/app/core/logging.py
backend/app/core/security.py
backend/app/core/database.py
backend/app/core/exceptions.py

Endpoints:

GET /health
GET /ready

Seguridad mínima

secretos fuera del repositorio;

CORS restringido;

validación de entrada;

logging sin secretos;

dependencias fijadas;

HTTPS preparado para producción.

Definition of Done

docker compose up

levanta frontend, backend y PostgreSQL; /health y /ready devuelven 200; tests, ruff, mypy, eslint y TypeScript pasan.

Prompt IA

Ejecuta la Fase 0. No implementes lógica de negocio. Prioriza estructura, Docker, configuración, health checks, logging, linting, typing y tests. No introduzcas microservicios. Revisa que no existan secretos ni dependencias innecesarias.

FASE 1 — PROCESSOS CORE

Objetivo

Crear la infraestructura compartida por todas las apps.

Entidades

Organization
User
Membership
Role
Permission
App
Subscription
Integration
Notification
AuditEvent
FeatureFlag

Auth

Implementar login, logout, sesión/token, recuperación y arquitectura preparada para MFA.

Multi-tenancy

Toda query de negocio debe resolverse dentro de la organización actual. organization_id nunca se aceptará desde el frontend como autoridad.

RBAC

Roles iniciales:

owner
admin
manager
employee
viewer

Preparar:

accountant
tax_advisor
payroll
hr

Audit Log

Registrar actor, organización, acción, recurso, timestamp, resultado y metadata segura.

App Launcher

Permitir activación/desactivación de apps por organización.

Definition of Done

Un usuario puede autenticarse, entrar en una organización, recibir permisos, ver solo apps habilitadas y jamás acceder a otra organización.

Prompt IA

Implementa ProcessOS Core con multi-tenancy estricto, UUID, Organization, User, Membership, Role, Permission, App, AuditEvent y FeatureFlag. Crea tests específicos de aislamiento entre tenants. No avances hasta demostrar que una organización no puede leer datos de otra.

FASE 2 — COMMERCIAL OS / CRM

Objetivo

Crear el centro comercial de trabajo diario.

Entidades

Company
Contact
Activity
Task
Opportunity
PipelineStage
Call
Tag
Campaign

Pipeline

discovered
researched
qualified
call_pending
contacted
audit_sent
audit_completed
meeting
diagnosis
proposal
won
lost
nurturing

Today Dashboard

Mostrar llamadas, follow-ups vencidos, hot leads, auditorías, reuniones, propuestas y Next Best Actions.

Next Best Action

Todo lead activo debe tener:

next_best_action
next_action_at

Call Workspace

Resultados:

no_answer
call_back
wrong_contact
not_interested
interested
send_audit
meeting
discarded

Frontend

Kanban;

tabla;

Company 360;

activity timeline;

call workspace;

Today dashboard.

Definition of Done

El usuario puede llevar un lead desde Discovered hasta Won/Lost sin otra herramienta.

Prompt IA

Construye el Commercial OS. Prioriza Kanban, Company 360, llamadas, actividades, tareas, Today Dashboard y Next Best Action. No añadas scraping todavía. Debe ser utilizable introduciendo empresas manualmente.

FASE 3 — PROCESSOS AUDIT

Objetivo

Crear auditorías adaptativas para cualificar y preparar reuniones.

Entidades

Audit
AuditSession
Section
Question
QuestionOption
ConditionalRule
Answer
Score
Finding
Opportunity
MeetingBrief

Tipos

Express: 15–20 preguntas, ~5 minutos.
Professional: 40–60 preguntas, 10–15 minutos, branching.

Áreas

Business Context
Sales
Customer Service
Administration
Operations
Tools
Data
Reporting
Internal Communication
Repetitive Work
Management Priorities

Scores

Business Fit
Process Pain
Operational Maturity
Digital Maturity
Potential Impact
Urgency
Decision Capacity
Meeting Qualification

Meeting Brief

Known
Unknown
Findings
Hypotheses
Opportunities
Questions Missing
Agenda

Reglas

token público seguro y expirable;

autosave;

resume;

distinguir reported, observed, inferred, hypothesis, validated.

Definition of Done

Un lead recibe auditoría, la completa y CRM recibe scores, findings y Meeting Brief.

Prompt IA

Implementa Audit como motor de preguntas dinámicas almacenadas en datos/configuración. Añade branching, autosave, resume, scoring y Meeting Brief. No conviertas hipótesis en hechos.

FASE 4 — DISCOVERY & RESEARCH

Objetivo

Encontrar empresas y enriquecerlas.

Entidades

DiscoveryJob
CompanySource
ResearchJob
WebsiteAnalysis
ReviewAnalysis
Signal

Fuentes iniciales

CSV;

alta manual;

fuentes públicas permitidas;

después directorios, buscadores, OpenStreetMap y fuentes sectoriales.

Deduplicación

domain
phone
name + city
external_id

Research

Analizar home, servicios, contacto, about, booking, portal, blog, formularios, WhatsApp, chat, tecnologías, CTA y reseñas.

Seguridad

timeouts;

límites de tamaño;

SSRF protection;

retries limitados;

fallo aislado por empresa.

Definition of Done

Campaña → empresas → dedupe → research → señales en CRM.

Prompt IA

Implementa Discovery y Research como jobs resilientes. Un fallo no debe detener una campaña. Añade dedupe, timeout, retry y protección SSRF. Evidencia y hipótesis deben estar separadas.

FASE 5 — PROCESSOS TIME INTEGRATION

Objetivo

Integrar la app de fichajes existente.

Funciones

empleados;

entrada/salida;

jornadas;

incidencias;

histórico;

exportaciones.

Integración

Todo se mapea a organization_id y employee_id.

Eventos:

time.entry.created
time.entry.updated
time.period.closed

Definition of Done

Time funciona dentro del mismo login, organización y sistema de permisos que el resto de ProcessOS.

Prompt IA

Integra Time sin reescribir innecesariamente la app existente. Adapta identidad, organización, permisos y eventos. Mantén el dominio desacoplado de Payroll.

FASE 6 — DOCS & DOCUMENT INBOX

Objetivo

Crear la entrada universal de documentos.

Tipos

invoice
receipt
ticket
bank_statement
payroll
contract
tax_document
social_security
certificate
other

Flujo

upload
↓
security checks
↓
private storage
↓
metadata
↓
processing
↓
classification
↓
review / validated

Seguridad

private storage;

signed URLs temporales;

MIME validation;

size limits;

hashing;

permisos;

tenant isolation.

Estados

uploaded
processing
needs_review
validated
posted
duplicate
rejected

Definition of Done

El cliente puede subir documentación de forma segura y verla en un inbox estructurado.

Prompt IA

Implementa Docs con storage privado, signed URLs temporales, hashing, metadata y estados. Otros módulos deben consumir documentos mediante interfaces, sin acoplarse al proveedor de storage.

FASE 7 — FINANCE FOUNDATION

Objetivo

Crear el cockpit financiero.

Entidades

Customer
Supplier
Invoice
Expense
Payment
Transaction
Account
FinancialPeriod

KPIs

Gross Revenue
Net Revenue
Expenses
Profit
Margin
Cash
Receivables
Payables
Reserved Taxes
Real Available Cash

UX

No mostrar contabilidad técnica como interfaz principal. Mostrar: has facturado, has gastado, has ganado, debes reservar y puedes gastar.

Definition of Done

El usuario entiende su situación financiera y cada KPI puede rastrearse hasta movimientos de origen.

Prompt IA

Construye Finance independiente de Tax. Implementa facturas, gastos, pagos, cuentas y periodos. Cada KPI debe ser explicable. No mezcles reglas fiscales específicas todavía.

FASE 8 — DOCUMENT INTELLIGENCE

Objetivo

Convertir documentos en datos estructurados.

Pipeline

Document
↓
OCR / Vision
↓
Extraction
↓
Normalization
↓
Classification
↓
Confidence
↓
Human Validation
↓
Posting

Campos frecuentes:

supplier
tax_id
date
invoice_number
base
taxes
total
category

Reglas

guardar original y extracción separados;

confidence score;

baja confianza → revisión;

nunca inventar campos ausentes.

Definition of Done

El usuario sube una factura y recibe una extracción estructurada para confirmar.

Prompt IA

Implementa Document Intelligence desacoplado de proveedor OCR/IA. Guarda original y extracción por separado, confidence score y validación humana.

FASE 9 — TAX FOUNDATION

Objetivo

Crear la infraestructura fiscal auditable.

Entidades

TaxProfile
TaxPeriod
TaxRuleSet
TaxCalculation
TaxObligation
TaxReturn

Motor

tax_rules/
└── 2026/
    ├── iva/
    ├── irpf/
    ├── withholding/
    └── models/

Toda regla debe ser versionada.

Estados

estimated
review_required
ready
submitted
accepted
rejected

Explainability

Guardar inputs, rule_version, result y pendientes.

Definition of Done

El sistema puede preparar estimaciones fiscales reproducibles sin usar un LLM como calculadora fiscal.

Prompt IA

Construye Tax Foundation con reglas deterministas versionadas. Separa estimated de confirmed. No implementes reglas no documentadas ni uses IA como motor de cálculo.

FASE 10 — BANKING & RECONCILIATION

Objetivo

Relacionar movimientos bancarios con Finance.

MVP

Importación CSV/statement y entrada manual. Open Banking llegará después.

Entidades

BankAccount
BankTransaction
Reconciliation
ReconciliationRule

Estados

unmatched
suggested
matched
ignored
needs_review

Seguridad

Nunca almacenar credenciales bancarias.

Definition of Done

El usuario puede importar extractos, evitar duplicados y conciliar movimientos.

Prompt IA

Implementa Banking con importación primero. Separa BankTransaction del ledger. Añade sugerencias de conciliación y confirmación humana. Nunca almacenes credenciales bancarias.

FASE 11 — HR FOUNDATION

Objetivo

Crear el núcleo de empleados.

Entidades

Employee
Employment
Contract
Department
Position
Absence
VacationRequest
EmployeeDocument

Separar Employee de Employment para mantener historia contractual.

Datos sensibles

DNI/NIE;

NSS;

IBAN;

salario;

documentos.

Integración

HR
↓
Time
↓
Payroll
↓
Docs

Definition of Done

Un empleado tiene expediente digital, historial laboral y permisos correctos.

Prompt IA

Implementa HR como fuente maestra de empleados. Protege campos sensibles y separa Employee de Employment. No mezcles todavía cálculos de nómina.

FASE 12 — PAYROLL ENGINE

Objetivo

Crear un motor de nóminas determinista y auditable.

Entidades

PayrollRuleSet
PayrollPeriod
PayrollRun
Payslip
PayrollVariable
PayrollAdjustment

Inputs

Contrato, salario, horas, Time, ausencias, vacaciones, variables, retenciones, cotizaciones y convenio.

Reglas

payroll_rules/
└── 2026/
    ├── social_security/
    ├── withholding/
    ├── contracts/
    └── contributions/

collective_agreements/

Estados

draft
calculated
needs_review
approved
issued
paid

Cada línea debe explicar input, fórmula, rule_version y amount.

Definition of Done

Una nómina estándar puede reproducirse exactamente a partir de reglas y datos versionados.

Prompt IA

Construye Payroll Engine determinista y versionado. No hardcodees reglas en controllers. Añade tests fuertes antes de cualquier emisión real.

FASE 13 — EMPLOYEE ONBOARDING / OFFBOARDING

Objetivo

Automatizar el flujo administrativo laboral.

Onboarding

New Employee
↓
data
↓
documents
↓
contract
↓
validation
↓
official-action preparation
↓
authorization
↓
active

Offboarding

Motivo, fecha, vacaciones, nómina final, documentos y preparación de actuaciones oficiales.

Regla

Casos jurídicos delicados:

CRITICAL
→ especialista

Definition of Done

El expediente puede prepararse completamente sin ejecutar silenciosamente acciones críticas.

Prompt IA

Implementa onboarding/offboarding como workflows explícitos con estados, aprobaciones y audit log. Separa preparación de ejecución oficial.

FASE 14 — MANAGED SERVICE / GESTORÍA DIGITAL

Objetivo

Gestionar carteras de clientes por excepciones.

Dashboard interno

150 clients
127 OK
14 processing
6 waiting documents
2 review required
1 call recommended

Health Scores

Document Health
Tax Health
Finance Health
Payroll Health
Time Health
Compliance Health

Human Intervention Queue

call_required
tax_review
payroll_review
legal_review
document_issue
security_issue

KPI central

Human Minutes per Client per Month

Definition of Done

Un gestor administra cartera sin revisar manualmente todos los clientes.

Prompt IA

Implementa Managed Service con Management by Exception. Prioriza automáticamente clientes que requieren intervención humana y mide Human Minutes per Client.

FASE 15 — REPRESENTATION, CERTIFICATES & ADMINISTRATIVE STATUS

Objetivo

Centralizar poderes, autorizaciones, certificados y notificaciones.

Entidades

Representation
Authorization
CertificateMetadata
AdministrativeNotification
AdministrativeTask

Dashboard

AEAT representation       Active
TGSS authorization        Active
Certificate               Expires in 34 days
Notifications             1 new

Regla de seguridad

Preferir representación/autorización y proveedores seguros antes que almacenar certificados privados.

Definition of Done

El gestor conoce el estado administrativo de cada cliente desde ProcessOS.

Prompt IA

Implementa representación y estado administrativo como workflows y metadata. No almacenes material criptográfico sensible sin una arquitectura formal de custodia.

FASE 16 — COMPLIANCE

Objetivo

Crear un framework de obligaciones empresariales.

Dominios potenciales

Salary Register
Policies
Protocols
GDPR
Deadlines
Whistleblowing
Inspections
Certificates
Maintenance

Modelo

Requirement
Status
Responsible
Evidence
Deadline
Risk
Action

Definition of Done

El cliente ve qué obligaciones tiene, qué está cubierto, qué falta y qué vence.

Prompt IA

Implementa Compliance como Requirement + Evidence + Deadline + Status. Las reglas deben ser versionadas y revisables, no hardcodeadas en UI.

FASE 17 — BUSINESS INTELLIGENCE

Objetivo

Cruzar datos de toda la suite.

Ejemplos

Revenue +12%
Personnel Cost +18%
Margin 31% → 26%

Health Scores

Financial Health
Tax Health
HR Health
Documentation Health
Compliance Health
Operational Health

Toda recomendación debe indicar fuente, confianza y razón.

Definition of Done

ProcessOS ayuda a tomar decisiones y cada insight es explicable.

Prompt IA

Construye BI sobre datos existentes, sin duplicarlos. Distingue métricas deterministas, estimaciones e insights de IA. Cada insight debe enlazar a sus datos fuente.

FASE 18 — PARTNER EDITION

Objetivo

Permitir que gestorías utilicen ProcessOS para sus clientes.

Entidades

Partner
PartnerUser
ManagedOrganization
PortfolioAssignment
PartnerPlan

Funciones

multi-client;

asignación de gestores;

portfolio dashboard;

permisos;

SLA;

billing;

branding futuro.

Definition of Done

Un partner gestiona organizaciones asignadas sin escapar de su ámbito autorizado.

Prompt IA

Implementa Partner Edition sobre el Core existente. Refuerza aislamiento y delegación. No construyas una segunda identidad paralela.

FASE 19 — BILLING & APP MARKETPLACE

Objetivo

Monetizar apps y bundles.

Entidades

Plan
Price
Subscription
SubscriptionItem
Usage
AppEntitlement

Apps:

Time
Finance
Tax
HR
Payroll
Docs
Managed

Definition of Done

Una organización activa/desactiva apps según plan y permisos.

Prompt IA

Implementa Billing desacoplado del proveedor de pagos. Modela Plan, Price, Subscription y AppEntitlement antes de integrar Stripe u otro proveedor.

FASE 20 — SECURITY HARDENING

Objetivo

Preparar datos sensibles reales.

Requisitos

MFA
Step-Up Auth
Zero Trust
Least Privilege
Audit Logs
Anomaly Detection
Secret Management
Encrypted Backups
Restore Tests
SAST
Dependency Scan
Container Scan
Rate Limiting
WAF

Step-up para cambiar IBAN, presentar impuestos, crear admins, cambiar permisos, operaciones laborales oficiales y exports sensibles.

Pentest

Antes de producción sensible:

pentest externo;

tenant isolation test;

architecture review;

permission review.

Definition of Done

No se permite producción sensible hasta cerrar riesgos críticos.

Prompt IA

Ejecuta hardening sin añadir features. Audita auth, tenancy, permisos, secretos, documentos, sesiones, dependencias, backups y APIs. Crea tests negativos de acceso prohibido.

FASE 21 — OBSERVABILITY & RESILIENCE

Objetivo

Saber qué ocurre y recuperarse de fallos.

Implementar

structured logs
metrics
traces
job monitoring
error monitoring
integration health
queue health
alerts

Resiliencia

retries limitados;

idempotencia;

dead-letter pattern;

timeout;

circuit breaker cuando proceda.

Definition of Done

Los errores pueden diagnosticarse sin entrar manualmente en producción.

Prompt IA

Añade observabilidad sin contaminar dominio. Usa request IDs, job IDs y structured logging. Diseña retries e idempotencia explícitamente.

FASE 22 — PRODUCTION READINESS

Objetivo

Preparar operación profesional.

Checklist

migrations
backup
restore test
monitoring
alerts
CI/CD
staging
production env
secrets manager
rate limits
security review
legal review
privacy review
incident response

Runbooks

database outage
provider outage
security incident
data leak
failed migration
rollback
tax integration failure
payroll incident

Definition of Done

ProcessOS puede desplegarse, operarse y recuperarse profesionalmente.

Prompt IA

No añadas funcionalidades. Prepara despliegue reproducible, backups, restore, monitoring, runbooks, migrations, rollback, secrets y documentación operativa.

23. REGLAS DE CÓDIGO PARA TODAS LAS FASES

Backend

typing completo;

funciones pequeñas;

Pydantic en límites;

domain exceptions;

repository interfaces;

dependency inversion;

transacciones explícitas;

no business logic en routes;

no SQL disperso.

Frontend

TypeScript strict;

componentes pequeños;

server/client boundary explícita;

formularios validados;

loading/error/empty states;

accessibility básica;

permission guards.

DB

UUID;

timestamps;

migrations;

indexes;

constraints;

foreign keys;

organization_id;

soft delete solo si el dominio lo requiere.

24. FORMATO ADR

# ADR-XXX — Título

Status:
Context:
Decision:
Alternatives:
Consequences:
Security Impact:
Migration Impact:

ADRs iniciales:

ADR-001 Modular Monolith
ADR-002 PostgreSQL
ADR-003 Multi-tenancy
ADR-004 Private Documents
ADR-005 AI Provider Abstraction

25. DEFINITION OF DONE GLOBAL

Una feature no está terminada porque “se ve bien”.

[ ] requisito implementado
[ ] autorización correcta
[ ] tenant isolation
[ ] tests
[ ] lint
[ ] typing
[ ] error handling
[ ] logging
[ ] no secrets
[ ] migration revisada
[ ] docs actualizadas
[ ] edge cases
[ ] security impact revisado

Para features críticas:

[ ] human review
[ ] audit event
[ ] deterministic rule
[ ] versioned rule
[ ] rollback / recovery

26. PROMPT MAESTRO PARA CODEX / IA

Estás desarrollando ProcessOS, un Business Operating System modular y multi-tenant para autónomos y pymes. Trabaja únicamente sobre la fase que te indique y respeta PROCESSOS_AI_DEVELOPMENT_BY_PHASES.md como fuente de verdad técnica.

Antes de escribir código:

identifica el módulo afectado;

revisa arquitectura y contratos existentes;

explica brevemente qué archivos modificarás;

evita dependencias innecesarias.

Durante la implementación:

mantén el dominio desacoplado de frameworks;

aplica organization_id y autorización en backend;

no pongas lógica de negocio en routes;

añade typing y validación;

gestiona errores;

crea audit logs cuando corresponda;

no expongas secretos;

no uses IA para cálculos fiscales/laborales críticos.

Al finalizar:

ejecuta tests;

ejecuta lint;

ejecuta mypy/TypeScript;

revisa seguridad;

resume cambios;

indica riesgos pendientes.

Nunca implementes fases futuras de forma masiva sin indicación explícita.

27. ORDEN DE EJECUCIÓN

FASE 0   Foundation
FASE 1   Core
FASE 2   Commercial OS
FASE 3   Audit
FASE 4   Discovery & Research
FASE 5   Time Integration
FASE 6   Docs
FASE 7   Finance
FASE 8   Document Intelligence
FASE 9   Tax Foundation
FASE 10  Banking
FASE 11  HR
FASE 12  Payroll
FASE 13  Employee Workflows
FASE 14  Managed Service
FASE 15  Representation & Notifications
FASE 16  Compliance
FASE 17  Business Intelligence
FASE 18  Partner Edition
FASE 19  Billing & Marketplace
FASE 20  Security Hardening
FASE 21  Observability
FASE 22  Production Readiness

28. PRINCIPIO FINAL

ProcessOS no debe construirse intentando terminar toda la suite a la vez.

CORE SÓLIDO
↓
APP ÚTIL
↓
USO REAL
↓
INTEGRACIÓN
↓
AUTOMATIZACIÓN
↓
SEGURIDAD
↓
ESCALA

Cada fase debe dejar ProcessOS en un estado funcional, testeable y demostrable.

El objetivo no es producir más código.

El objetivo es construir un sistema:

seguro
modular
auditable
comprensible
automatizable
mantenible
escalable

capaz de mantener:

el negocio del cliente permanentemente bajo control.