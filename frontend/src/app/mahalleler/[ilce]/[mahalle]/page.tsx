import Link from "next/link";
import type { Metadata } from "next";

export const revalidate = 3600;
const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

async function getMahalle(ilce: string, mahalle: string) {
  try {
    const res = await fetch(`${API}/api/v1/rehber/mahalle/${ilce}/${mahalle}`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    const j = await res.json();
    return j?.bulundu === false ? null : j;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: any): Promise<Metadata> {
  const { ilce, mahalle } = await params;
  const d = await getMahalle(ilce, mahalle);
  if (!d) return { title: "Mahalle bulunamadı | rayic.org" };
  const fiyat = d.satilik_tlm2 ? `${d.satilik_tlm2.toLocaleString("tr-TR")} ₺/m²` : "";
  return {
    title: `${d.ad}, ${d.ilce} — m² Fiyatı, Kira, Deprem Riski | rayic.org`,
    description:
      `${d.ad} (${d.ilce}) mahallesinde satılık m² fiyatı ${fiyat}, kira rayici, ` +
      `İBB deprem senaryosuna göre bina hasar beklentisi, kıyıya ve raylı sisteme uzaklık. ` +
      `Ücretsiz mahalle profili.`,
    alternates: { canonical: `/mahalleler/${ilce}/${mahalle}` },
  };
}

function tl(n?: number | null) {
  return typeof n === "number" ? n.toLocaleString("tr-TR") : "—";
}

export default async function MahallePage({ params }: any) {
  const { ilce, mahalle } = await params;
  const d = await getMahalle(ilce, mahalle);

  if (!d) {
    return (
      <main className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="text-2xl font-extrabold">Mahalle bulunamadı</h1>
        <Link href="/mahalleler" className="text-[#047857] font-bold text-sm">← Tüm ilçeler</Link>
      </main>
    );
  }

  const dep = d.deprem;
  const dag = d.fiyat_dagilimi;
  const dem = d.ilce_demografi;

  // Arama motorları için yapılandırılmış veri
  const ld = {
    "@context": "https://schema.org",
    "@type": "Place",
    name: `${d.ad} Mahallesi, ${d.ilce}, İstanbul`,
    address: {
      "@type": "PostalAddress",
      addressLocality: d.ilce,
      addressRegion: "İstanbul",
      addressCountry: "TR",
    },
    ...(d.lat && d.lng
      ? { geo: { "@type": "GeoCoordinates", latitude: d.lat, longitude: d.lng } }
      : {}),
  };

  return (
    <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }}
      />

      <nav className="text-[11px] font-bold text-slate-500">
        <Link href="/mahalleler" className="hover:text-[#047857]">Mahalle Rehberi</Link>
        <span className="mx-1.5">/</span>
        <Link href={`/mahalleler/${ilce}`} className="hover:text-[#047857]">{d.ilce}</Link>
        <span className="mx-1.5">/</span>
        <span className="text-[#111827]">{d.ad}</span>
      </nav>

      <header className="space-y-2">
        <h1 className="text-3xl font-extrabold text-[#111827] font-display tracking-tight">
          {d.ad} Mahallesi — {d.ilce}
        </h1>
        <p className="text-sm text-slate-700 font-medium leading-relaxed max-w-3xl">
          {d.ad}, {d.ilce} ilçesinde yer alır
          {d.kiyiya_km != null ? `; kıyıya yaklaşık ${d.kiyiya_km} km` : ""}
          {d.rayli_sisteme_km != null ? `, en yakın raylı sistem durağına ${d.rayli_sisteme_km} km` : ""}
          {" "}mesafededir. Aşağıdaki veriler ücretsizdir ve kayıt gerektirmez.
        </p>
      </header>

      <section aria-labelledby="fiyat" className="light-card p-5 bg-white border border-[#E5E7EB]">
        <h2 id="fiyat" className="text-sm font-extrabold text-[#111827] uppercase mb-3">
          Konut Fiyatları (Ağustos 2026)
        </h2>
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-bold">
          <div className="p-3 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB]">
            <dt className="text-[9px] text-slate-500 uppercase">Satılık</dt>
            <dd className="text-[#111827] font-mono text-base">{tl(d.satilik_tlm2)} ₺/m²</dd>
          </div>
          <div className="p-3 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB]">
            <dt className="text-[9px] text-slate-500 uppercase">Kiralık</dt>
            <dd className="text-[#047857] font-mono text-base">{tl(d.kiralik_tlm2)} ₺/m²</dd>
          </div>
          <div className="p-3 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB]">
            <dt className="text-[9px] text-slate-500 uppercase">Amortisman</dt>
            <dd className="text-[#111827] font-mono text-base">
              {d.amortisman_yil ? `${d.amortisman_yil} yıl` : "—"}
            </dd>
          </div>
          <div className="p-3 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB]">
            <dt className="text-[9px] text-slate-500 uppercase">100 m² kira</dt>
            <dd className="text-[#111827] font-mono text-base">
              {d.kiralik_tlm2 ? `${tl(Math.round(d.kiralik_tlm2 * 100))} ₺` : "—"}
            </dd>
          </div>
        </dl>

        {dag && (
          <div className={`mt-3 p-3 rounded-lg border text-[11px] leading-relaxed ${
            dag.heterojen ? "bg-amber-50 border-amber-300 text-amber-900"
                          : "bg-[#FAF8F5] border-[#E5E7EB] text-slate-700"}`}>
            <strong>Mahalle içi fiyat aralığı:</strong> {tl(dag.p25)} – {tl(dag.p75)} ₺/m²
            {" "}(medyan {tl(dag.medyan)}, {dag.ilan_n} ilan).{" "}
            {dag.heterojen
              ? "Bu mahalle fiyat açısından heterojendir; tek bir m² fiyatı yanıltıcı olabilir, konuma göre ciddi fark vardır."
              : "Mahalle görece türdeştir, fiyatlar birbirine yakındır."}
          </div>
        )}
      </section>

      {dep && (
        <section aria-labelledby="deprem" className="light-card p-5 bg-white border border-[#E5E7EB]">
          <h2 id="deprem" className="text-sm font-extrabold text-[#111827] uppercase mb-1">
            Deprem Riski — İBB Olası Deprem Senaryosu
          </h2>
          <p className="text-[11px] text-slate-600 mb-3">
            Beklenen büyük Marmara depreminde bu mahalle için öngörülen değerler.
          </p>
          <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-bold">
            {([
              ["Çok ağır hasar", `${tl(dep.cok_agir_hasarli_bina)} bina`],
              ["Ağır hasar", `${tl(dep.agir_hasarli_bina)} bina`],
              ["Orta hasar", `${tl(dep.orta_hasarli_bina)} bina`],
              ["Ağır+ oranı", dep.agir_ustu_bina_orani_pct != null ? `%${dep.agir_ustu_bina_orani_pct}` : "—"],
              ["Can kaybı öngörüsü", tl(dep.can_kaybi)],
              ["Ağır yaralı", tl(dep.agir_yarali)],
              ["Geçici barınma", tl(dep.gecici_barinma)],
            ] as [string, any][]).map(([k, v]) => (
              <div key={k} className="p-3 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB]">
                <dt className="text-[9px] text-slate-500 uppercase">{k}</dt>
                <dd className="text-[#111827] font-mono">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-2 text-[10px] text-slate-500">{dep.kaynak}</p>
        </section>
      )}

      {d.tsunami && (
        <section className="p-4 bg-sky-50 border border-sky-300 rounded-xl text-[11px] text-sky-900">
          <h2 className="text-xs font-extrabold uppercase mb-1">Tsunami / Su Basma</h2>
          <p>MeTHuVA taşkın çalışmasına göre bu kıyı mahallesi için veri mevcuttur:{" "}
            {typeof d.tsunami === "object" ? JSON.stringify(d.tsunami) : String(d.tsunami)}</p>
        </section>
      )}

      {dem && (
        <section aria-labelledby="nufus" className="light-card p-5 bg-white border border-[#E5E7EB]">
          <h2 id="nufus" className="text-sm font-extrabold text-[#111827] uppercase mb-1">
            {d.ilce} Nüfus ve Yaş Yapısı ({dem.yil})
          </h2>
          <p className="text-[11px] text-slate-600 mb-3">
            Nüfus verisi ilçe düzeyindedir; mahalle kırılımı resmî açık veride yayınlanmamaktadır.
          </p>
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
                <dd className="text-[#111827] font-mono">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-2 text-[10px] text-slate-500">{dem.kaynak}</p>
        </section>
      )}

      <section className="p-5 bg-[#111827] text-white rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-extrabold font-display">
            {d.ad}&apos;de bir konutun değerini öğrenin
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Adresinizi seçin; ada/parsel, imar durumu, deprem ve konum analizi otomatik gelsin.
          </p>
        </div>
        <Link
          href="/"
          className="px-5 py-3 bg-[#047857] hover:bg-[#065F46] rounded-xl text-xs font-extrabold uppercase tracking-wider shrink-0"
        >
          Ücretsiz Değerleme
        </Link>
      </section>
    </main>
  );
}
