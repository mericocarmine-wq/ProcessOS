"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";

type CompanyDetail = { id: string; name: string; domain: string | null; phone: string | null; email: string | null; city: string | null; source: string; qualification_score: number; opportunity: { stage: string; next_best_action: string | null; next_action_at: string | null }; activities: Array<{ kind: string; summary: string; created_at: string }> };

export default function CompanyPage() {
  const { id } = useParams<{ id: string }>();
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [error, setError] = useState("");
  const load = useCallback(async () => { const response = await fetch(`/api/commercial/companies/${id}`, { cache: "no-store" }); if (response.ok) setCompany(await response.json()); else setError("No se pudo cargar la empresa."); }, [id]);
  useEffect(() => {
    // The company detail is synchronized after route hydration.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);
  async function saveCall(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = event.currentTarget; const data = new FormData(form); const response = await fetch(`/api/commercial/companies/${id}/calls`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ outcome: data.get("outcome"), notes: data.get("notes") || null, next_best_action: data.get("action"), next_action_at: new Date(String(data.get("due"))).toISOString() }) }); if (!response.ok) { setError("No se pudo registrar la llamada."); return; } form.reset(); await load(); }
  if (!company) return <main className="detail-shell"><Link href="/">← Volver al CRM</Link><p>{error || "Cargando ficha 360…"}</p></main>;
  return <main className="detail-shell"><header className="detail-header"><div><Link href="/">← Volver al CRM</Link><p className="eyebrow">Empresa 360</p><h1>{company.name}</h1><p className="muted">{company.domain || "Sin dominio"} · {company.city || "Sin ubicación"}</p></div><span className="score">{company.qualification_score}<small>score</small></span></header><div className="detail-grid"><section className="card"><h2>Contexto comercial</h2><dl><div><dt>Etapa</dt><dd>{company.opportunity.stage}</dd></div><div><dt>Siguiente acción</dt><dd>{company.opportunity.next_best_action}</dd></div><div><dt>Origen</dt><dd>{company.source}</dd></div><div><dt>Contacto</dt><dd>{company.email || company.phone || "Pendiente"}</dd></div></dl></section><section className="card"><h2>Registrar llamada</h2><form onSubmit={(event) => void saveCall(event)}><label>Resultado<select name="outcome" required><option value="no_answer">Sin respuesta</option><option value="call_back">Volver a llamar</option><option value="wrong_contact">Contacto incorrecto</option><option value="not_interested">No interesado</option><option value="interested">Interesado</option><option value="send_audit">Enviar auditoría</option><option value="meeting">Reunión</option><option value="discarded">Descartado</option></select></label><label>Notas<textarea name="notes" rows={3} /></label><label>Siguiente acción<input name="action" required /></label><label>Fecha objetivo<input name="due" type="datetime-local" required /></label><button>Guardar llamada</button></form>{error && <p className="error">{error}</p>}</section><section className="card timeline"><h2>Actividad</h2>{company.activities.length ? company.activities.map((activity, index) => <article key={`${activity.created_at}-${index}`}><i /><div><strong>{activity.summary}</strong><time>{new Date(activity.created_at).toLocaleString("es-ES")}</time></div></article>) : <p className="empty">Aún no hay actividad.</p>}</section></div></main>;
}
