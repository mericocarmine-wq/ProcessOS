import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "ProcessOS Commercial",
  description: "Control comercial interno de ProcessOS.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
