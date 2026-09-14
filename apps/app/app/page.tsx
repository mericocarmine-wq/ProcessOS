"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type Identity = { email: string; organization_name: string; role: string; permissions: string[] };
type Opportunity = { stage: string; next_best_action: string | null; next_action_at: string | null };
type Company = { id: string; name: string; domain: string | null; city: string | null; qualification_score: number; opportunity: Opportunity };
type Today = { calls_completed: number; overdue_actions: number; hot_leads: number; next_actions: Array<{ company_id: string; company_name: string; action: string; due_at: string }> };
type DiscoveryJob = { id: string; source_type: string; status: string; processed_count: number; created_count: number; duplicate_count: number; failed_count: number };
type View = "today" | "discovery" | "pipeline" | "companies" | "calls";

const stages = ["discovered", "researched", "qualified", "call_pending", "contacted", "audit_sent", "audit_completed", "meeting", "diagnosis", "proposal", "won", "lost", "nurturing"];
const names: Record<string, string> = { discovered: "Descubierta", researched: "Investigada", qualified: "Cualificada", call_pending: "Llamada pendiente", contacted: "Contactada", audit_sent: "Auditoría enviada", audit_completed: "Auditoría completada", meeting: "Reunión", diagnosis: "Diagnóstico", proposal: "Propuesta", won: "Ganada", lost: "Perdida", nurturing: "Nutrición" };
const viewNames: Record<View, string> = { today: "Hoy", discovery: "Discovery", pipeline: "Pipeline", companies: "Empresas", calls: "Llamadas" };

export default function Home() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [today, setToday] = useState<Today | null>(null);
  const [jobs, setJobs] = useState<DiscoveryJob[]>([]);
  const [view, setView] = useState<View>("today");
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");

  const loadCommercial = useCallback(async () => {
    const [list, summary, recentJobs] = await Promise.all([fetch("/api/commercial/companies", { cache: "no-store" }), fetch("/api/commercial/today", { cache: "no-store" }), fetch("/api/commercial/discovery/jobs", { cache: "no-store" })]);
    if (list.ok) setCompanies(await list.json());
    if (summary.ok) setToday(await summary.json());
    if (recentJobs.ok) setJobs(await recentJobs.json());
  }, []);

  const loadSession = useCallback(async () => {
    const response = await fetch("/api/session/me", { cache: "no-store" });
    if (!response.ok) { setIdentity(null); setLoading(false); return; }
    const current = await response.json(); setIdentity(current);
    if (current.permissions.includes("commercial.read")) await loadCommercial();
    setLoading(false);
  }, [loadCommercial]);

  useEffect(() => {
    // Session synchronization starts after the browser mounts the client shell.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadSession().catch(() => { setError("No se pudo conectar con ProcessOS."); setLoading(false); });
  }, [loadSession]);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); const data = new FormData(event.currentTarget);
    const response = await fetch("/api/session/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: data.get("email"), password: data.get("password"), organization_slug: data.get("organization") }) });
    if (!response.ok) { setError("Credenciales u organización incorrectas."); return; }
    setLoading(true); await loadSession();
  }

  async function createCompany(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    const response = await fetch("/api/commercial/companies", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: data.get("name"), domain: data.get("domain") || null, city: data.get("city") || null, next_best_action: data.get("action"), next_action_at: new Date(String(data.get("due"))).toISOString() }) });
    if (!response.ok) { setError("No se pudo crear la empresa."); return; }
    form.reset(); await loadCommercial();
  }

  async function move(company: Company, stage: string) {
    const terminal = ["won", "lost"].includes(stage);
    await fetch(`/api/commercial/companies/${company.id}/stage`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ stage, next_best_action: terminal ? null : company.opportunity.next_best_action, next_action_at: terminal ? null : company.opportunity.next_action_at }) });
    await loadCommercial();
  }

  async function importCsv(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    const lines = String(data.get("csv")).trim().split(/\r?\n/).filter(Boolean);
    const headers = lines.shift()?.split(",").map((item) => item.trim().toLowerCase()) ?? [];
    const records = lines.map((line) => { const values = line.split(",").map((item) => item.trim()); return Object.fromEntries(headers.map((header, index) => [header, values[index] || null])); });
    const response = await fetch("/api/commercial/discovery/import", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ provider: "csv", records }) });
    if (!response.ok) { setError("No se pudo importar el CSV. Comprueba las columnas."); return; }
    form.reset(); await loadCommercial();
  }

  async function searchCompanies(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSearching(true); setError("");
    const data = new FormData(event.currentTarget);
    const response = await fetch("/api/commercial/discovery/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ provider: "openstreetmap", sector: data.get("sector"), city: data.get("city"), limit: Number(data.get("limit")) }) });
    if (!response.ok) { const problem = await response.json(); setError(problem.detail || "La fuente no respondió."); setSearching(false); return; }
    await loadCommercial(); setSearching(false);
  }

  async function logout() { await fetch("/api/session/logout", { method: "POST" }); setIdentity(null); setCompanies([]); }
  const columns = useMemo(() => stages.map((stage) => ({ stage, items: companies.filter((company) => company.opportunity.stage === stage) })), [companies]);

  if (loading) return <main className="shell"><p role="status">Comprobando sesión…</p></main>;
  if (!identity) return <main className="shell"><header className="brand">ProcessOS <span>Commercial</span></header><section className="panel login-panel"><p className="eyebrow">Acceso interno</p><h1>Control comercial</h1><p className="muted">Prospección, cualificación y seguimiento en un entorno independiente.</p><form onSubmit={(event) => void login(event)}><label>Email<input name="email" type="email" required /></label><label>Organización<input name="organization" required /></label><label>Contraseña<input name="password" type="password" required /></label>{error && <p className="error" role="alert">{error}</p>}<button>Entrar</button></form><Link href="/forgot-password">He olvidado mi contraseña</Link></section></main>;

  return <main className="crm-shell"><aside className="sidebar"><div className="brand">ProcessOS <span>Commercial</span></div><nav>{(Object.keys(viewNames) as View[]).map((item) => <button key={item} className={view === item ? "active" : ""} onClick={() => setView(item)}>{viewNames[item]}</button>)}</nav><div className="account"><small>{identity.organization_name}</small><span>{identity.email}</span><button onClick={() => void logout()}>Salir</button></div></aside><section className="workspace"><header className="workspace-header"><div><p className="eyebrow">CRM propio · {identity.role}</p><h1>{view === "today" ? "Tu foco de hoy" : viewNames[view]}</h1></div><span className="status-pill">● Operativo</span></header>{error && <p className="error">{error}</p>}
    {view === "today" && <><div className="metrics"><article><small>Llamadas realizadas</small><strong>{today?.calls_completed ?? 0}</strong></article><article><small>Seguimientos vencidos</small><strong>{today?.overdue_actions ?? 0}</strong></article><article><small>Leads calientes</small><strong>{today?.hot_leads ?? 0}</strong></article><article><small>Pipeline activo</small><strong>{companies.filter((c) => !["won", "lost"].includes(c.opportunity.stage)).length}</strong></article></div><section className="card"><div className="section-title"><h2>Siguientes mejores acciones</h2><span>{today?.next_actions.length ?? 0} pendientes</span></div><div className="action-list">{today?.next_actions.length ? today.next_actions.map((item) => <Link href={`/companies/${item.company_id}`} key={item.company_id}><strong>{item.company_name}</strong><span>{item.action}</span><time>{new Date(item.due_at).toLocaleString("es-ES")}</time></Link>) : <p className="empty">Todo al día. Añade una empresa para empezar.</p>}</div></section></>}
    {view === "discovery" && <div className="discovery-grid"><section className="card search-card"><p className="eyebrow">OpenStreetMap · ODbL</p><h2>Buscar empresas</h2><p className="muted">Selecciona una actividad y una localidad. Los resultados entrarán directamente al proceso de deduplicación.</p><form onSubmit={(event) => void searchCompanies(event)}><label>Sector<select name="sector" required defaultValue="accounting"><option value="accounting">Asesorías y contabilidad</option><option value="clinic">Clínicas y consultas</option><option value="construction">Construcción</option><option value="law">Despachos jurídicos</option><option value="real_estate">Inmobiliarias</option><option value="restaurant">Restauración</option><option value="hotel">Hoteles y alojamientos</option><option value="hairdresser">Peluquerías</option><option value="car_repair">Talleres de vehículos</option></select></label><label>Ciudad o municipio<input name="city" required placeholder="Madrid" /></label><label>Máximo de resultados<input name="limit" type="number" min="1" max="100" defaultValue="30" required /></label><button disabled={searching}>{searching ? "Buscando y deduplicando…" : "Buscar empresas"}</button></form><small className="attribution">Datos © colaboradores de OpenStreetMap.</small></section><section className="card"><p className="eyebrow">Archivo propio</p><h2>Importar CSV</h2><p className="muted">Columnas: name, domain, phone, city, email, external_id.</p><form onSubmit={(event) => void importCsv(event)}><label>Contenido CSV<textarea name="csv" rows={8} required placeholder={"name,domain,phone,city\nEmpresa Demo,empresa.es,+34910000000,Madrid"} /></label><button>Deduplicar e importar</button></form></section><section className="card jobs-card"><div className="section-title"><h2>Procesos recientes</h2><span>{jobs.length} jobs</span></div><div className="job-list">{jobs.length ? jobs.map((job) => <article key={job.id}><div><strong>{job.source_type.toUpperCase()}</strong><small>{job.status}</small></div><span>{job.processed_count} revisadas</span><span>{job.created_count} nuevas</span><span>{job.duplicate_count} duplicadas</span><span>{job.failed_count} fallidas</span></article>) : <p className="empty">Aún no hay búsquedas.</p>}</div></section></div>}
    {view === "pipeline" && <div className="kanban">{columns.map((column) => <section className="kanban-column" key={column.stage}><header><strong>{names[column.stage]}</strong><span>{column.items.length}</span></header>{column.items.map((company) => <article key={company.id}><Link href={`/companies/${company.id}`}><h3>{company.name}</h3></Link><p>{company.opportunity.next_best_action ?? "Sin acción"}</p><select aria-label={`Etapa de ${company.name}`} value={company.opportunity.stage} onChange={(event) => void move(company, event.target.value)}>{stages.map((stage) => <option key={stage} value={stage}>{names[stage]}</option>)}</select></article>)}</section>)}</div>}
    {view === "companies" && <div className="split"><section className="card"><h2>Nueva empresa</h2><form onSubmit={(event) => void createCompany(event)} className="company-form"><label>Empresa<input name="name" required /></label><label>Dominio<input name="domain" placeholder="empresa.es" /></label><label>Ciudad<input name="city" /></label><label>Siguiente acción<input name="action" required placeholder="Llamar al responsable" /></label><label>Fecha objetivo<input name="due" type="datetime-local" required /></label><button>Añadir al pipeline</button></form></section><section className="card table-card"><div className="section-title"><h2>Cartera</h2><span>{companies.length} empresas</span></div><table><thead><tr><th>Empresa</th><th>Etapa</th><th>Próxima acción</th></tr></thead><tbody>{companies.map((company) => <tr key={company.id}><td><Link href={`/companies/${company.id}`}>{company.name}</Link><small>{company.domain}</small></td><td><span className="stage">{names[company.opportunity.stage]}</span></td><td>{company.opportunity.next_best_action}</td></tr>)}</tbody></table></section></div>}
    {view === "calls" && <section className="card"><div className="section-title"><h2>Cola de llamadas</h2><span>Prioridad por vencimiento</span></div><div className="call-queue">{companies.filter((c) => !["won", "lost"].includes(c.opportunity.stage)).sort((a,b) => String(a.opportunity.next_action_at).localeCompare(String(b.opportunity.next_action_at))).map((company) => <Link href={`/companies/${company.id}`} key={company.id}><span className="avatar">{company.name.slice(0,2).toUpperCase()}</span><div><strong>{company.name}</strong><small>{company.opportunity.next_best_action}</small></div><span>Abrir ficha →</span></Link>)}</div></section>}
  </section></main>;
}
