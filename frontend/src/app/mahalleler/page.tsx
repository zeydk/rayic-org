import Link from "next/link";
import type { Metadata } from "next";

// SEO: bu bölüm paywall'suzdur ve sunucuda render edilir (arama motorları
// içeriği doğrudan görür). Veriler gerçek kaynaklardan gelir; uydurma
// gösterge yoktur.
export const metadata: Metadata = {
  title: "İstanbul Mahalle ve İlçe Rehberi — Fiyat, Deprem Riski, Demografi | rayic.org",
  description:
    "İstanbul'un 39 ilçesi ve 479 mahallesi için güncel satılık/kiralık m² fiyatları, " +
    "İBB deprem senaryosu verileri, nüfus ve yaş yapısı, kıyı ve raylı sistem mesafeleri. " +
    "Ücretsiz ve kayıtsız.",
  alternates: { canonical: "/mahalleler" },
};

export const revalidate = 3600;

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

async function getIlceler() {
  try {
    const res = await fetch(`${API}/api/v1/rehber/ilceler`, { next: { revalidate: 3600 } });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

function tl(n?: number | null) {
  return typeof n === "number" ? n.toLocaleString("tr-TR") : "—";
}

export default async function MahallelerPage() {
  const data = await getIlceler();
  const ilceler = data?.ilceler ?? [];

  return (
    <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      <header className="space-y-3">
        <span className="light-badge text-[10px]">ÜCRETSİZ REHBER · KAYIT GEREKTİRMEZ</span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-[#111827] font-display tracking-tight">
          İstanbul Mahalle ve İlçe Rehberi
        </h1>
        <p className="text-sm text-slate-700 font-medium leading-relaxed max-w-3xl">
          39 ilçe ve {data?.meta?.mahalle_sayisi ?? 479} mahalle için güncel <strong>satılık ve
          kiralık m² fiyatları</strong>, <strong>İBB olası deprem senaryosu</strong> verileri,
          <strong> nüfus ve yaş yapısı</strong>, kıyıya ve raylı sisteme uzaklık.
          Tamamı ücretsizdir.
        </p>
      </header>

      <section aria-labelledby="ilce-listesi" className="space-y-4">
        <h2 id="ilce-listesi" className="text-xl font-extrabold text-[#111827] font-display">
          İlçeler
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {ilceler.map((i: any) => (
            <Link
              key={i.slug}
              href={`/mahalleler/${i.slug}`}
              className="light-card p-4 bg-white border border-[#E5E7EB] hover:border-[#111827] transition-all block"
            >
              <div className="flex items-baseline justify-between gap-2">
                <h3 className="text-base font-extrabold text-[#111827]">{i.ad}</h3>
                <span className="text-[10px] text-slate-500 font-bold">
                  {i.mahalle_sayisi} mahalle
                </span>
              </div>
              <dl className="mt-2 grid grid-cols-2 gap-2 text-[11px] font-bold">
                <div>
                  <dt className="text-slate-500 uppercase text-[9px]">Satılık</dt>
                  <dd className="text-[#111827] font-mono">{tl(i.medyan_satilik_tlm2)} ₺/m²</dd>
                </div>
                <div>
                  <dt className="text-slate-500 uppercase text-[9px]">Kiralık</dt>
                  <dd className="text-[#047857] font-mono">{tl(i.medyan_kiralik_tlm2)} ₺/m²</dd>
                </div>
                {i.demografi?.medyan_yas && (
                  <div>
                    <dt className="text-slate-500 uppercase text-[9px]">Medyan yaş</dt>
                    <dd className="text-[#111827] font-mono">{i.demografi.medyan_yas}</dd>
                  </div>
                )}
                {i.demografi?.nufus && (
                  <div>
                    <dt className="text-slate-500 uppercase text-[9px]">Nüfus</dt>
                    <dd className="text-[#111827] font-mono">{tl(i.demografi.nufus)}</dd>
                  </div>
                )}
              </dl>
            </Link>
          ))}
        </div>
        {ilceler.length === 0 && (
          <p className="text-sm text-slate-600">Rehber verisi şu anda yüklenemedi.</p>
        )}
      </section>

      <section className="p-4 bg-[#FAF8F5] border border-[#E5E7EB] rounded-xl text-[11px] text-slate-600 leading-relaxed">
        <h2 className="text-xs font-extrabold text-[#111827] uppercase mb-1">Veri kaynakları</h2>
        <ul className="list-disc pl-5 space-y-0.5">
          {(data?.meta?.kaynaklar ?? []).map((k: string) => (
            <li key={k}>{k}</li>
          ))}
        </ul>
        {data?.meta?.not && <p className="mt-2 italic">{data.meta.not}</p>}
      </section>
    </main>
  );
}
