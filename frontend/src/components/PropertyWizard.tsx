"use client";

import React, { useEffect, useState } from "react";
import {
  Target, Map, MapPin, Layers, Signpost, Home, LayoutGrid, CalendarClock,
  Calculator, Ruler, CheckCircle2, ArrowRight, ArrowLeft, AlertCircle,
  Loader2, HelpCircle, Building2,
} from "lucide-react";
import SearchableSelect, { sentenceCase } from "./SearchableSelect";

/**
 * Adım adım konut girişi.
 *
 * Önceki tasarımda tek ekranda ilçe+mahalle+ada/parsel+adres+oda birlikte
 * soruluyordu; adres iki ayrı yerde isteniyordu ve uzun listelerde seçim
 * zordu. Artık her soru KENDİ EKRANINDA, kendi ikonuyla ve tek odakla.
 *
 * Akış: amaç -> ilçe -> mahalle -> ada/parsel (biliyorsa) -> sokak -> kapı
 *       -> oda/daire -> bina yaşı -> fiyat/m² -> arsa payı
 * Ada/parsel bilinmiyorsa sokak+kapı ZORUNLU (imar bilgisi için gerekli);
 * biliniyorsa sokak/kapı adımları atlanır.
 */

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export interface ParsedData {
  user_role: "buyer" | "renter" | "seller";
  price: number; net_m2: number; gross_m2: number; building_age: number;
  floor: string; floor_category: string; room_count: string;
  total_land_m2: number; land_share_num: number; land_share_den: number;
  district: string; neighborhood: string;
  full_address?: string; street?: string; door_no?: string; apt_no?: string;
  ada_no?: string; parsel_no?: string; lat?: number; lng?: number;
  missing_fields: string[];
}

interface Props {
  onComplete: (d: ParsedData) => void;
  loading?: boolean;
}

type AdimId =
  | "amac" | "ilce" | "mahalle" | "adaparsel" | "sokak" | "kapi"
  | "oda" | "yas" | "fiyat" | "arsa";

const ADIMLAR: { id: AdimId; baslik: string; alt: string; icon: any }[] = [
  { id: "amac", baslik: "İşlem amacınız nedir?", alt: "Raporu size göre hazırlayalım", icon: Target },
  { id: "ilce", baslik: "Konut hangi ilçede?", alt: "İstanbul'un 39 ilçesi", icon: Map },
  { id: "mahalle", baslik: "Hangi mahallede?", alt: "Resmî mahalle kayıtları", icon: MapPin },
  { id: "adaparsel", baslik: "Ada / parsel biliyor musunuz?", alt: "En kesin yöntem — tapunuzda yazar", icon: Layers },
  { id: "sokak", baslik: "Sokak veya cadde", alt: "Resmî adres kayıtlarından seçin", icon: Signpost },
  { id: "kapi", baslik: "Kapı numarası", alt: "Binanın konumu buradan bulunur", icon: Home },
  { id: "oda", baslik: "Oda düzeni ve daire no", alt: "Dairenin iç özellikleri", icon: LayoutGrid },
  { id: "yas", baslik: "Bina yaşı", alt: "Bilmiyorsanız geçebilirsiniz", icon: CalendarClock },
  { id: "fiyat", baslik: "Fiyat ve metrekare", alt: "İlan bilgileri", icon: Calculator },
  { id: "arsa", baslik: "Arsa payı", alt: "Kentsel dönüşüm hesabı için", icon: Ruler },
];

const num = (v: string) => Number(String(v).replace(/\D/g, "")) || 0;
const fmt = (v: string) => {
  const n = String(v).replace(/\D/g, "");
  return n ? new Intl.NumberFormat("tr-TR").format(Number(n)) : "";
};

export default function PropertyWizard({ onComplete, loading = false }: Props) {
  const [i, setI] = useState(0);
  const [hata, setHata] = useState<string | null>(null);

  const [rol, setRol] = useState<"buyer" | "renter" | "seller">("buyer");
  const [ilceler, setIlceler] = useState<any[]>([]);
  const [mahalleler, setMahalleler] = useState<any[]>([]);
  const [sokaklar, setSokaklar] = useState<any[]>([]);
  const [kapilar, setKapilar] = useState<any[]>([]);
  const [ilce, setIlce] = useState(""); const [mahalle, setMahalle] = useState("");
  const [sokak, setSokak] = useState(""); const [kapi, setKapi] = useState("");
  const [yuk, setYuk] = useState<string | null>(null);
  const [cozum, setCozum] = useState<any>(null);

  const [apBiliyor, setApBiliyor] = useState<boolean | null>(null);
  const [ada, setAda] = useState(""); const [parsel, setParsel] = useState("");
  const [oda, setOda] = useState(""); const [daire, setDaire] = useState("");
  const [yas, setYas] = useState(""); const [yasBilinmiyor, setYasBilinmiyor] = useState(false);
  const [kat, setKat] = useState("ara_kat");
  const [fiyat, setFiyat] = useState(""); const [netM2, setNetM2] = useState("");
  const [brutM2, setBrutM2] = useState("");
  const [arsa, setArsa] = useState(""); const [pay, setPay] = useState(""); const [payda, setPayda] = useState("");

  useEffect(() => {
    fetch(`${API}/api/v1/adres/ilceler`).then((r) => r.json())
      .then((d) => setIlceler(d.ilceler || [])).catch(() => setIlceler([]));
  }, []);

  const adIlce = ilceler.find((x) => String(x.id) === ilce)?.name || "";
  const adMahalle = mahalleler.find((x) => String(x.id) === mahalle)?.name || "";
  const adSokak = sokaklar.find((x) => String(x.id) === sokak)?.name || "";
  const adKapi = kapilar.find((x) => String(x.id) === kapi)?.name || "";

  const secIlce = async (id: string) => {
    setIlce(id); setMahalle(""); setSokak(""); setKapi("");
    setMahalleler([]); setSokaklar([]); setKapilar([]); setCozum(null);
    if (!id) return;
    setYuk("mahalle");
    try {
      const d = await (await fetch(`${API}/api/v1/adres/mahalleler?ilce_id=${id}`)).json();
      setMahalleler(d.mahalleler || []);
    } finally { setYuk(null); }
  };

  const secMahalle = async (id: string) => {
    setMahalle(id); setSokak(""); setKapi(""); setSokaklar([]); setKapilar([]); setCozum(null);
    if (!id) return;
    setYuk("sokak");
    try {
      const d = await (await fetch(`${API}/api/v1/adres/sokaklar?mahalle_id=${id}`)).json();
      setSokaklar(d.sokaklar || []);
    } finally { setYuk(null); }
  };

  const secSokak = async (id: string) => {
    setSokak(id); setKapi(""); setKapilar([]); setCozum(null);
    if (!id || !mahalle) return;
    setYuk("kapi");
    try {
      const d = await (await fetch(`${API}/api/v1/adres/kapilar?mahalle_id=${mahalle}&sokak_id=${id}`)).json();
      setKapilar(d.kapilar || []);
    } finally { setYuk(null); }
  };

  const secKapi = async (id: string) => {
    setKapi(id); setCozum(null);
    if (!id) return;
    setYuk("coz");
    try {
      const d = await (await fetch(
        `${API}/api/v1/adres/coz?ilce_id=${ilce}&mahalle_id=${mahalle}&sokak_id=${sokak}&kapi_id=${id}`)).json();
      setCozum(d);
      if (d?.bulundu) {
        if (d.ada_no) setAda(String(d.ada_no));
        if (d.parsel_no) setParsel(String(d.parsel_no));
      }
    } finally { setYuk(null); }
  };

  // Ada/parsel biliniyorsa sokak+kapı adımları atlanır
  const gorunur = ADIMLAR.filter((a) =>
    apBiliyor === true ? a.id !== "sokak" && a.id !== "kapi" : true);
  const adim = gorunur[i];
  const sonAdim = i === gorunur.length - 1;

  const dogrula = (): boolean => {
    switch (adim.id) {
      case "ilce": if (!ilce) return !!setHata("Lütfen ilçe seçin."); break;
      case "mahalle": if (!mahalle) return !!setHata("Lütfen mahalle seçin."); break;
      case "adaparsel":
        if (apBiliyor === null) return !!setHata("Lütfen bir seçim yapın.");
        if (apBiliyor && (!ada.trim() || !parsel.trim()))
          return !!setHata("Ada ve parsel numarasını girin veya “Bilmiyorum”u seçin.");
        break;
      case "sokak": if (!sokak) return !!setHata("Lütfen sokak/cadde seçin."); break;
      case "kapi": if (!kapi) return !!setHata("Lütfen kapı numarası seçin."); break;
      case "oda": if (!oda) return !!setHata("Lütfen oda düzenini seçin."); break;
      case "yas":
        if (!yasBilinmiyor && (yas === "" || Number(yas) < 0))
          return !!setHata("Bina yaşını girin veya “Bilmiyorum”u işaretleyin.");
        break;
      case "fiyat":
        if (num(fiyat) <= 0) return !!setHata("Geçerli bir ilan fiyatı girin.");
        if (num(netM2) <= 0) return !!setHata("Geçerli bir net m² girin.");
        break;
      case "arsa":
        if (num(arsa) <= 0) return !!setHata("Toplam arsa büyüklüğünü girin.");
        if (num(pay) <= 0 || num(payda) <= 0) return !!setHata("Arsa payı (pay/payda) girin.");
        break;
    }
    setHata(null);
    return true;
  };

  const ileri = () => {
    if (!dogrula()) return;
    if (sonAdim) {
      onComplete({
        user_role: rol,
        price: num(fiyat), net_m2: num(netM2), gross_m2: num(brutM2) || Math.round(num(netM2) * 1.2),
        building_age: yasBilinmiyor ? 20 : Number(yas),
        floor: "3", floor_category: kat, room_count: oda,
        total_land_m2: num(arsa), land_share_num: num(pay), land_share_den: num(payda),
        district: sentenceCase(adIlce), neighborhood: sentenceCase(adMahalle),
        street: adSokak ? sentenceCase(adSokak) : undefined,
        door_no: adKapi || undefined, apt_no: daire || undefined,
        ada_no: ada || undefined, parsel_no: parsel || undefined,
        lat: cozum?.lat, lng: cozum?.lng,
        missing_fields: yasBilinmiyor ? ["building_age"] : [],
      });
      return;
    }
    setI(i + 1);
  };

  const Ikon = adim.icon;
  const yuzde = Math.round(((i + 1) / gorunur.length) * 100);

  const inputCls =
    "w-full bg-white border border-[#D1D5DB] rounded-xl p-3 text-sm text-[#111827] font-bold focus:outline-none focus:border-[#111827]";

  return (
    <div className="light-card p-5 sm:p-7 bg-white border border-[#E5E7EB] space-y-6 max-w-3xl mx-auto">
      {/* İlerleme */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-[10px] font-extrabold uppercase tracking-wider text-slate-500">
          <span>Adım {i + 1} / {gorunur.length}</span>
          <span>%{yuzde} tamamlandı</span>
        </div>
        <div className="h-1.5 bg-[#E5E7EB] rounded-full overflow-hidden">
          <div className="h-full bg-[#047857] transition-all duration-300" style={{ width: `${yuzde}%` }} />
        </div>
        <div className="flex gap-1 flex-wrap pt-1">
          {gorunur.map((a, idx) => {
            const A = a.icon;
            const gecti = idx < i, aktif = idx === i;
            return (
              <button
                key={a.id}
                type="button"
                onClick={() => idx < i && setI(idx)}
                disabled={idx > i}
                title={a.baslik}
                className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
                  aktif ? "bg-[#111827] text-white"
                    : gecti ? "bg-[#047857]/10 text-[#047857] hover:bg-[#047857]/20 cursor-pointer"
                    : "bg-[#F3F4F6] text-slate-300"}`}
              >
                {gecti ? <CheckCircle2 className="w-3.5 h-3.5" /> : <A className="w-3.5 h-3.5" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Başlık */}
      <div className="flex items-start gap-3">
        <div className="w-11 h-11 rounded-xl bg-[#047857]/10 flex items-center justify-center shrink-0">
          <Ikon className="w-5 h-5 text-[#047857]" />
        </div>
        <div>
          <h2 className="text-xl font-extrabold text-[#111827] font-display leading-tight">{adim.baslik}</h2>
          <p className="text-xs text-slate-600 font-medium mt-0.5">{adim.alt}</p>
        </div>
      </div>

      {/* İçerik */}
      <div className="min-h-[190px]">
        {adim.id === "amac" && (
          <div className="grid gap-2.5">
            {([
              ["buyer", "🔑 Konut alacağım", "Almadan önce gerçek değerini ve risklerini göreyim"],
              ["renter", "🏠 Konut kiralayacağım", "Rayiç kirayı ve mahalle bilgilerini inceleyeyim"],
              ["seller", "💼 Satıcı / kiraya verenim", "Mülkümün gerçek değerini öğreneyim"],
            ] as [any, string, string][]).map(([v, b, a]) => (
              <button key={v} type="button" onClick={() => setRol(v)}
                className={`p-4 rounded-xl border-2 text-left transition-all ${
                  rol === v ? "border-[#047857] bg-[#047857]/5" : "border-[#E5E7EB] hover:border-[#111827]"}`}>
                <div className="text-sm font-extrabold text-[#111827]">{b}</div>
                <div className="text-[11px] text-slate-600 mt-0.5">{a}</div>
              </button>
            ))}
          </div>
        )}

        {adim.id === "ilce" && (
          <SearchableSelect label="İlçe" value={ilce} options={ilceler}
            onSelect={secIlce} loading={ilceler.length === 0}
            placeholder="İlçe seçin veya yazın (ör. kadikoy)" />
        )}

        {adim.id === "mahalle" && (
          <SearchableSelect label="Mahalle" value={mahalle} options={mahalleler}
            onSelect={secMahalle} loading={yuk === "mahalle"} disabled={!ilce}
            placeholder="Mahalle seçin veya yazın (ör. eren)" />
        )}

        {adim.id === "adaparsel" && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2.5">
              <button type="button" onClick={() => setApBiliyor(true)}
                className={`p-4 rounded-xl border-2 text-left ${apBiliyor === true ? "border-[#047857] bg-[#047857]/5" : "border-[#E5E7EB] hover:border-[#111827]"}`}>
                <Layers className="w-4 h-4 text-[#047857] mb-1" />
                <div className="text-sm font-extrabold">Biliyorum</div>
                <div className="text-[11px] text-slate-600">Tapumda yazıyor</div>
              </button>
              <button type="button" onClick={() => { setApBiliyor(false); setAda(""); setParsel(""); }}
                className={`p-4 rounded-xl border-2 text-left ${apBiliyor === false ? "border-[#047857] bg-[#047857]/5" : "border-[#E5E7EB] hover:border-[#111827]"}`}>
                <HelpCircle className="w-4 h-4 text-slate-500 mb-1" />
                <div className="text-sm font-extrabold">Bilmiyorum</div>
                <div className="text-[11px] text-slate-600">Adresimden bulun</div>
              </button>
            </div>
            {apBiliyor === true && (
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Ada No</label>
                  <input value={ada} onChange={(e) => setAda(e.target.value)} placeholder="Örn: 412" className={inputCls} /></div>
                <div><label className="text-slate-600 block mb-1 uppercase text-[10px] font-bold">Parsel No</label>
                  <input value={parsel} onChange={(e) => setParsel(e.target.value)} placeholder="Örn: 20" className={inputCls} /></div>
              </div>
            )}
            {apBiliyor === false && (
              <p className="text-[11px] text-slate-600 bg-[#FAF8F5] border border-[#E5E7EB] rounded-xl p-3">
                Sorun değil — sonraki adımlarda sokak ve kapı numaranızı seçeceksiniz,
                ada/parseli ve imar bilgisini biz bulacağız.
              </p>
            )}
          </div>
        )}

        {adim.id === "sokak" && (
          <SearchableSelect label="Sokak / Cadde" value={sokak} options={sokaklar}
            onSelect={secSokak} loading={yuk === "sokak"} disabled={!mahalle}
            placeholder="Sokak seçin veya yazın (ör. bagdat)"
            emptyHint="Bu mahalle için sokak listesi alınamadı. Geri dönüp tekrar deneyin." />
        )}

        {adim.id === "kapi" && (
          <div className="space-y-3">
            <SearchableSelect label="Kapı No" value={kapi} options={kapilar}
              onSelect={secKapi} loading={yuk === "kapi"} disabled={!sokak}
              placeholder="Kapı numarası seçin veya yazın" />
            {yuk === "coz" && (
              <p className="text-[11px] text-slate-600 flex items-center gap-1.5">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Konum ve ada/parsel çözümleniyor…
              </p>
            )}
            {cozum?.bulundu && (
              <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-xl text-[11px] text-emerald-900 font-medium">
                ✅ <strong>Adres resmî kayıttan bulundu.</strong> Kapı {cozum.kapi_no} →{" "}
                <strong>Ada {cozum.ada_no} / Parsel {cozum.parsel_no}</strong>
                {cozum.tapu_mahalle ? ` (${sentenceCase(cozum.tapu_mahalle)} tapu mahallesi)` : ""}.
                Konum binanın kendi koordinatıdır.
              </div>
            )}
            {cozum && !cozum.bulundu && (
              <div className="p-3 bg-amber-50 border border-amber-300 rounded-xl text-[11px] text-amber-900">
                ⚠️ {cozum.mesaj}
              </div>
            )}
          </div>
        )}

        {adim.id === "oda" && (
          <div className="space-y-4">
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">Oda Düzeni</label>
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                {["1+1", "2+1", "3+1", "4+1", "4+2"].map((o) => (
                  <button key={o} type="button" onClick={() => setOda(o)}
                    className={`py-3 rounded-xl border-2 text-sm font-extrabold ${
                      oda === o ? "border-[#047857] bg-[#047857]/5 text-[#047857]" : "border-[#E5E7EB] hover:border-[#111827]"}`}>
                    {o}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">Daire No (opsiyonel)</label>
              <input value={daire} onChange={(e) => setDaire(e.target.value)} placeholder="Örn: 12" className={`${inputCls} sm:w-48`} />
            </div>
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">Kat Konumu</label>
              <select value={kat} onChange={(e) => setKat(e.target.value)} className={inputCls}>
                <option value="bodrum">Bodrum / Giriş altı</option>
                <option value="zemin">Zemin kat</option>
                <option value="ara_kat">Ara kat</option>
                <option value="ust_kat">Üst kat</option>
                <option value="dubleks">Dubleks / Çatı</option>
              </select>
            </div>
          </div>
        )}

        {adim.id === "yas" && (
          <div className="space-y-3">
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">Bina Yaşı (yıl)</label>
              <input value={yas} disabled={yasBilinmiyor}
                onChange={(e) => setYas(e.target.value.replace(/\D/g, ""))}
                placeholder="Örn: 12" className={`${inputCls} sm:w-48 ${yasBilinmiyor ? "bg-slate-100 text-slate-400" : ""}`} />
            </div>
            <label className="flex items-center gap-2 text-xs font-bold text-slate-700 cursor-pointer">
              <input type="checkbox" checked={yasBilinmiyor}
                onChange={(e) => { setYasBilinmiyor(e.target.checked); if (e.target.checked) setYas(""); }} />
              Bilmiyorum
            </label>
            {yasBilinmiyor && (
              <p className="text-[11px] text-slate-600 bg-[#FAF8F5] border border-[#E5E7EB] rounded-xl p-3">
                Sorun değil — İstanbul ortalaması (20 yıl) kullanılacak ve raporda
                bu varsayım açıkça belirtilecek.
              </p>
            )}
          </div>
        )}

        {adim.id === "fiyat" && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-3">
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">İlan Fiyatı (TL)</label>
              <input value={fmt(fiyat)} onChange={(e) => setFiyat(e.target.value)} placeholder="Örn: 15.000.000" className={inputCls} />
            </div>
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">Net m²</label>
              <input value={netM2} onChange={(e) => setNetM2(e.target.value.replace(/\D/g, ""))} placeholder="120" className={inputCls} />
            </div>
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">Brüt m² (ops.)</label>
              <input value={brutM2} onChange={(e) => setBrutM2(e.target.value.replace(/\D/g, ""))} placeholder="145" className={inputCls} />
            </div>
          </div>
        )}

        {adim.id === "arsa" && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">Toplam Arsa (m²)</label>
              <input value={arsa} onChange={(e) => setArsa(e.target.value.replace(/\D/g, ""))} placeholder="2400" className={inputCls} />
            </div>
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">Arsa Payı — Pay</label>
              <input value={pay} onChange={(e) => setPay(e.target.value.replace(/\D/g, ""))} placeholder="15" className={inputCls} />
            </div>
            <div>
              <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">Arsa Payı — Payda</label>
              <input value={payda} onChange={(e) => setPayda(e.target.value.replace(/\D/g, ""))} placeholder="240" className={inputCls} />
            </div>
            <p className="sm:col-span-3 text-[11px] text-slate-600">
              Bu bilgiler tapunuzda ve yönetim planında yer alır; kentsel dönüşüm
              senaryosunu hesaplamak için kullanılır.
            </p>
          </div>
        )}
      </div>

      {hata && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-300 rounded-xl text-xs font-bold text-red-800">
          <AlertCircle className="w-4 h-4 shrink-0" /> {hata}
        </div>
      )}

      {/* Özet şeridi */}
      {(adIlce || adMahalle) && (
        <div className="flex flex-wrap gap-1.5 text-[10px] font-bold">
          {[
            adIlce && sentenceCase(adIlce),
            adMahalle && sentenceCase(adMahalle),
            adSokak && sentenceCase(adSokak),
            adKapi && `Kapı ${adKapi}`,
            ada && parsel && `Ada ${ada}/${parsel}`,
          ].filter(Boolean).map((t) => (
            <span key={String(t)} className="px-2 py-1 bg-[#FAF8F5] border border-[#E5E7EB] rounded-lg text-slate-700">
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Gezinme */}
      <div className="flex items-center justify-between gap-3 pt-1">
        <button type="button" disabled={i === 0}
          onClick={() => { setHata(null); setI(Math.max(0, i - 1)); }}
          className="px-4 py-2.5 rounded-xl text-xs font-bold border border-[#D1D5DB] text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5" /> Geri
        </button>
        <button type="button" onClick={ileri} disabled={loading}
          className="px-6 py-3 rounded-xl bg-[#111827] hover:bg-[#047857] text-white text-xs font-extrabold uppercase tracking-wider flex items-center gap-2 transition-colors disabled:opacity-60">
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Hesaplanıyor…</>
            : sonAdim ? <><Building2 className="w-4 h-4" /> Raporu Oluştur</>
            : <>İleri <ArrowRight className="w-3.5 h-3.5" /></>}
        </button>
      </div>
    </div>
  );
}
