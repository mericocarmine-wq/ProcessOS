"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

export default function ForgotPassword() {
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const response = await fetch("/api/password-recovery", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: data.get("email") }),
    });
    setMessage(response.ok ? "Si la cuenta existe, recibirás un enlace temporal." : "La recuperación no está disponible. Contacta con administración.");
  }

  return <main className="shell"><section className="panel login-panel"><p className="eyebrow">Recuperación</p><h1>Restablecer acceso</h1><form onSubmit={(event) => void submit(event)}><label>Email<input name="email" type="email" autoComplete="email" required /></label><button type="submit">Enviar enlace</button></form>{message && <p role="status">{message}</p>}<Link href="/">Volver al acceso</Link></section></main>;
}
