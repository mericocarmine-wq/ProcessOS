"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

type Identity = { email: string; organization_name: string; role: string; permissions: string[] };
type EnabledApp = { code: string; name: string };

export default function Home() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [apps, setApps] = useState<EnabledApp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadSession() {
    const response = await fetch("/api/session/me", { cache: "no-store" });
    if (!response.ok) {
      setIdentity(null);
      setLoading(false);
      return;
    }
    setIdentity(await response.json());
    const appsResponse = await fetch("/api/core/apps", { cache: "no-store" });
    if (appsResponse.ok) setApps(await appsResponse.json());
    setLoading(false);
  }

  useEffect(() => {
    // State updates happen after network I/O; this is the initial session synchronization.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadSession().catch(() => {
      setError("No se pudo conectar con ProcessOS.");
      setLoading(false);
    });
  }, []);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    const response = await fetch("/api/session/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: data.get("email"),
        password: data.get("password"),
        organization_slug: data.get("organization"),
      }),
    });
    if (!response.ok) {
      setError("Credenciales u organización incorrectas.");
      return;
    }
    setLoading(true);
    await loadSession();
  }

  async function logout() {
    await fetch("/api/session/logout", { method: "POST" });
    setIdentity(null);
    setApps([]);
  }

  return (
    <main className="shell">
      <header className="brand">ProcessOS <span>Commercial</span></header>
      {loading ? <p role="status">Comprobando sesión…</p> : identity ? (
        <section className="panel dashboard">
          <div><p className="eyebrow">{identity.organization_name}</p><h1>Control comercial</h1><p className="muted">{identity.email} · {identity.role}</p></div>
          <button type="button" className="secondary" onClick={() => void logout()}>Salir</button>
          <div className="apps" aria-label="Aplicaciones habilitadas">
            {apps.length ? apps.map((app) => <article key={app.code}><strong>{app.name}</strong><small>{app.code}</small></article>) : <p className="muted">No hay aplicaciones habilitadas.</p>}
          </div>
        </section>
      ) : (
        <section className="panel login-panel">
          <p className="eyebrow">Acceso interno</p><h1>Control comercial</h1>
          <p className="muted">Scraping, cualificación y seguimiento en un entorno independiente.</p>
          <form onSubmit={(event) => void login(event)}>
            <label>Email<input name="email" type="email" autoComplete="email" required /></label>
            <label>Organización<input name="organization" autoComplete="organization" required /></label>
            <label>Contraseña<input name="password" type="password" autoComplete="current-password" required /></label>
            {error && <p className="error" role="alert">{error}</p>}
            <button type="submit">Entrar</button>
          </form>
          <Link href="/forgot-password">He olvidado mi contraseña</Link>
        </section>
      )}
    </main>
  );
}
