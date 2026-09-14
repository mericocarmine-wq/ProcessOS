"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

export default function ResetPassword() {
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const response = await fetch("/api/password-reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: new URLSearchParams(window.location.search).get("token"),
        new_password: data.get("password"),
      }),
    });
    setMessage(response.ok ? "Contraseña actualizada. Ya puedes iniciar sesión." : "El enlace no es válido o ha caducado.");
  }

  return <main className="shell"><section className="panel login-panel"><p className="eyebrow">Nuevo acceso</p><h1>Elige una contraseña</h1><form onSubmit={(event) => void submit(event)}><label>Nueva contraseña<input name="password" type="password" minLength={12} autoComplete="new-password" required /></label><button type="submit">Guardar contraseña</button></form>{message && <p role="status">{message}</p>}<Link href="/">Volver al acceso</Link></section></main>;
}
