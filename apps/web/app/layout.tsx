import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "ProcessOS",
  description: "Tu negocio, permanentemente bajo control.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}

