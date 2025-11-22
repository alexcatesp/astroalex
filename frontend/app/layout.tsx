import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Astroalex - Astrophotography Processing Pipeline",
  description: "Your intelligent astrophotography processing pipeline, automated and efficient.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
