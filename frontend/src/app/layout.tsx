import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "rayic.org | Real Estate Valuation & TCMB Macro Analytics",
  description: "Algorithmic real estate valuation system incorporating TCMB KFE Macro Index, urban transformation simulator, and spatial POI layer.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
        <link
          href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css"
          rel="stylesheet"
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[#FAF8F5] text-[#111827] antialiased selection:bg-[#111827] selection:text-[#FAF8F5]">
        {children}
      </body>
    </html>
  );
}
