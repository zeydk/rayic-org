import Link from "next/link";
import type { Metadata } from "next";

export const revalidate = 3600;
const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

async function getIlce(slug: string) {
  try {
    const res = await fetch(`${API}/api/v1/rehber/ilce/${slug}`, { next: { revalidate: 3600 } });
    if (!res.ok) return null;
    const j = await res.json();
    return j?.bulundu === false ? null : j;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: any): Promise<Metadata> {
  const { ilce } = await params;
  const d = await getIlce(ilce);
  const ad = d?.ad ?? ilce;
  return {
    title: `${ad} Mahalleleri — m² Fiyatları, Deprem Riski ve Nüfus | rayic.org`,
    description:
      `${ad} ilçesindeki mahallelerin güncel satılık ve kiralık m² fiyatları, ` +
      `İBB deprem senaryosuna göre bina hasar oranları, nüfus ve yaş yapısı, ` +
      `kıyıya ve raylı sisteme uzaklık. Ücretsiz mahalle rehberi.`,
    alternates: { canonical: `/mahalleler/${ilce}` },
  };
}

function tl(n?: number | null) {
  return typeof n === "number" ? n.toLocaleString("tr-TR") : "—";
}

export default async function IlcePage({ params }: any) {
  const { ilce } = await params;
  const d = await getIlce(ilce);

  if (!d) {
    return (
      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="text-2xl font-extrabold">İlçe bulunamadı</h1>
        <Link href="/mahalleler" className="text-[#047857] font-bold text-sm">
          ← Tüm ilçeler
        </Link>
      </main>
    );
  }

  const dem = d.demografi;
  const mahalleler = d.mahalleler ?? [];

  return (
    <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      <nav className="text-[11px] font-bold text-slate-500">
        <Link href="/mahalleler" className="hover:text-[#047857]">Mahalle Rehberi</Link>
        <span className="mx-1.5">/</span>
        <span className="text-[#111827]">{d.ad}</span>
      </nav>

      <header className="space-y-2">
        <h1 className="text-3xl font-extrabold text-[#111827] font-display tracking-tight">
          {d.ad} Mahalleleri
        </h1>
        <p className="text-sm text-slate-700 font-medium">
          {mahalleler.length} mahalle · güncel m² fiyatları, deprem senaryosu ve konum verileri
        </p>
      </header>

      {dem && (
        <section aria-labelledby="demo" className="light-card p-5 bg-white border border-[#E5E7EB]">
          <h2 id="demo" className="text-sm font-extrabold text-[#111827] uppercase mb-3">
            {d.ad} Nüfus ve Yaş Yapısı ({dem.yil})
          </h2>
          <dl className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs font-bold">
            {([
              ["Nüfus", tl(dem.nufus)],
              ["Medyan yaş", dem.medyan_yas],
              ["0-19 yaş", `%${dem.cocuk_genc_orani_pct}`],
              ["20-39 yaş", `%${dem.genc_yetiskin_orani_pct}`],
              ["65+ yaş", `%${dem.yasli_65_orani_pct}`],
              ["Erkek oranı", `%${dem.erkek_orani_pct}`],
            ] as [string, any][]).map(([k, v]) => (
              <div key={k} className="p-2.5 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB]">
                <dt className="text-[9px] text-slate-500 uppercase">{k}</dt>
                <dd className="text-[#111827] font-mono text-sm">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-2 text-[10px] text-slate-500">{dem.kaynak}</p>
        </section>
      )}

      <section aria-labelledby="mah" className="space-y-3">
        <h2 id="mah" className="text-xl font-extrabold text-[#111827] font-display">
          Mahalleler
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-bold border-collapse min-w-[640px]">
            <thead>
              <tr className="bg-[#FAF8F5] text-slate-600 uppercase text-[10px]">
                <th className="text-left p-2.5 border border-[#E5E7EB]">Mahalle</th>
                <th className="text-right p-2.5 border border-[#E5E7EB]">Satılık ₺/m²</th>
                <th className="text-right p-2.5 border border-[#E5E7EB]">Kiralık ₺/m²</th>
                <th className="text-right p-2.5 border border-[#E5E7EB]">Amortisman</th>
                <th className="text-right p-2.5 border border-[#E5E7EB]">Kıyı km</th>
                <th className="text-right p-2.5 border border-[#E5E7EB]">Raylı km</th>
                <th className="text-right p-2.5 border border-[#E5E7EB]">Ağır+ hasar</th>
              </tr>
            </thead>
            <tbody>
              {mahalleler.map((m: any) => (
                <tr key={m.slug} className="hover:bg-[#FAF8F5]">
                  <td className="p-2.5 border border-[#E5E7EB]">
                    <Link
                      href={`/mahalleler/${ilce}/${m.slug}`}
                      className="text-[#047857] hover:underline font-extrabold"
                    >
                      {m.ad}
                    </Link>
                  </td>
                  <td className="p-2.5 border border-[#E5E7EB] text-right font-mono">{tl(m.satilik_tlm2)}</td>
                  <td className="p-2.5 border border-[#E5E7EB] text-right font-mono">{tl(m.kiralik_tlm2)}</td>
                  <td className="p-2.5 border border-[#E5E7EB] text-right font-mono">
                    {m.amortisman_yil ? `${m.amortisman_yil} yıl` : "—"}
                  </td>
                  <td className="p-2.5 border border-[#E5E7EB] text-right font-mono">{m.kiyiya_km ?? "—"}</td>
                  <td className="p-2.5 border border-[#E5E7EB] text-right font-mono">{m.rayli_sisteme_km ?? "—"}</td>
                  <td className="p-2.5 border border-[#E5E7EB] text-right font-mono">
                    {m.deprem?.agir_ustu_bina_orani_pct != null ? `%${m.deprem.agir_ustu_bina_orani_pct}` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[10px] text-slate-500">
          &quot;Ağır+ hasar&quot;: İBB olası deprem senaryosunda ağır ve çok ağır hasar görmesi
          beklenen binaların, hasar gören toplam bina içindeki payı.
        </p>
      </section>
    </main>
  );
}
