"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { Search, Check, ChevronDown, Loader2 } from "lucide-react";

/**
 * Aranabilir seçim kutusu.
 *
 * NEDEN: İBB adres listeleri çok uzun (Bağdat Cad. tek başına 461 kapı,
 * bir mahallede 60+ sokak). Kullanıcının listeyi kaydırarak "Erenköy"ü
 * bulması yerine "eren" yazınca süzülmesi gerekiyor.
 *
 * Türkçe duyarlı arama: "sisli" yazınca "ŞİŞLİ", "cinar" yazınca "ÇINAR"
 * bulunur (aksan/İ-ı farkları normalize edilir).
 */

export function trNorm(s: string): string {
  return (s || "")
    .toLocaleLowerCase("tr")
    .replace(/ı/g, "i").replace(/İ/g, "i")
    .replace(/ş/g, "s").replace(/ğ/g, "g")
    .replace(/ü/g, "u").replace(/ö/g, "o")
    .replace(/ç/g, "c").replace(/â/g, "a")
    .replace(/[-_.]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** "BAĞDAT CAD." -> "Bağdat Cad."  (kısaltmalar ve tek harfler korunur) */
export function sentenceCase(s: string): string {
  if (!s) return "";
  return s
    .toLocaleLowerCase("tr")
    .split(" ")
    .map((w) => {
      if (!w) return w;
      // 19 Mayıs gibi sayıyla başlayanlar aynı kalsın
      if (/^\d/.test(w)) return w;
      return w.charAt(0).toLocaleUpperCase("tr") + w.slice(1);
    })
    .join(" ");
}

export interface Secenek {
  id: string | number;
  name: string;
}

interface Props {
  label: string;
  value: string;
  options: Secenek[];
  onSelect: (id: string) => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  emptyHint?: string;
}

export default function SearchableSelect({
  label, value, options, onSelect,
  disabled = false, loading = false,
  placeholder = "Seçiniz veya yazarak arayın…",
  emptyHint = "Sonuç bulunamadı.",
}: Props) {
  const [acik, setAcik] = useState(false);
  const [q, setQ] = useState("");
  const kutu = useRef<HTMLDivElement>(null);

  const secili = options.find((o) => String(o.id) === String(value));

  useEffect(() => {
    const dis = (e: MouseEvent) => {
      if (kutu.current && !kutu.current.contains(e.target as Node)) setAcik(false);
    };
    document.addEventListener("mousedown", dis);
    return () => document.removeEventListener("mousedown", dis);
  }, []);

  const suzulmus = useMemo(() => {
    if (!q.trim()) return options;
    const n = trNorm(q);
    // Baştan eşleşenler önce gelsin ("eren" -> "Erenköy" üstte)
    const bas: Secenek[] = [];
    const ic: Secenek[] = [];
    for (const o of options) {
      const on = trNorm(o.name);
      if (on.startsWith(n)) bas.push(o);
      else if (on.includes(n)) ic.push(o);
    }
    return [...bas, ...ic];
  }, [q, options]);

  const kapali = disabled || loading;

  return (
    <div ref={kutu} className="relative">
      <label className="text-slate-600 block mb-1.5 uppercase text-[10px] font-bold">
        {label}
        {options.length > 0 && <span className="text-slate-400 ml-1">({options.length})</span>}
      </label>

      <button
        type="button"
        disabled={kapali}
        onClick={() => { setAcik((a) => !a); setQ(""); }}
        className={`w-full flex items-center justify-between gap-2 bg-white border rounded-xl p-3 text-left text-sm font-bold transition-all ${
          kapali
            ? "border-[#E5E7EB] bg-slate-100 text-slate-400 cursor-not-allowed"
            : acik
            ? "border-[#111827] text-[#111827]"
            : "border-[#D1D5DB] text-[#111827] hover:border-[#111827]"
        }`}
      >
        <span className="truncate">
          {loading ? "Yükleniyor…" : secili ? sentenceCase(secili.name) : placeholder}
        </span>
        {loading
          ? <Loader2 className="w-4 h-4 animate-spin text-slate-400 shrink-0" />
          : <ChevronDown className={`w-4 h-4 shrink-0 transition-transform ${acik ? "rotate-180" : ""}`} />}
      </button>

      {acik && !kapali && (
        <div className="absolute z-40 mt-1 w-full bg-white border border-[#111827] rounded-xl shadow-xl overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2 border-b border-[#E5E7EB] bg-[#FAF8F5]">
            <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <input
              autoFocus
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Yazarak arayın…"
              className="w-full bg-transparent text-sm font-bold text-[#111827] focus:outline-none"
            />
          </div>
          <ul className="max-h-64 overflow-y-auto" role="listbox">
            {suzulmus.map((o) => {
              const sec = String(o.id) === String(value);
              return (
                <li key={o.id}>
                  <button
                    type="button"
                    onClick={() => { onSelect(String(o.id)); setAcik(false); setQ(""); }}
                    className={`w-full text-left px-3 py-2.5 text-sm font-bold flex items-center justify-between gap-2 transition-colors ${
                      sec ? "bg-[#047857] text-white" : "text-[#111827] hover:bg-[#FAF8F5]"
                    }`}
                  >
                    <span className="truncate">{sentenceCase(o.name)}</span>
                    {sec && <Check className="w-4 h-4 shrink-0" />}
                  </button>
                </li>
              );
            })}
            {suzulmus.length === 0 && (
              <li className="px-3 py-4 text-xs text-slate-500 font-medium text-center">{emptyHint}</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
