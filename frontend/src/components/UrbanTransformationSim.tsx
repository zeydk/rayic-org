"use client";

import React, { useState } from "react";
import { Hammer, TrendingUp, Sparkles, AlertCircle, ArrowRight, Download, CheckCircle2, FileText, MapPin, Layers } from "lucide-react";
import ReportPaywall from "./ReportPaywall";

import dynamic from "next/dynamic";

const LeafletPolygonMap = dynamic(() => import("./LeafletPolygonMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-100">
      <span className="text-sm font-mono animate-pulse">Harita Yükleniyor...</span>
    </div>
  )
});

interface UrbanTransformationSimProps {
  urban: any;
  onShareChange?: (newShareRatio: number) => void;
}

export default function UrbanTransformationSim({ urban, onShareChange }: UrbanTransformationSimProps) {
  const [unlocked, setUnlocked] = useState(false);

  if (!urban) return null;

  const {
    district = "Maltepe",
    neighborhood = "Çınar",
    ada_no = "2104",
    parsel_no = "15",
    existing_net_m2 = 95,
    existing_gross_m2 = 115,
    building_age = 28,
    contractor_share_ratio = 0.50,
    new_apartment_net_m2 = 85,
    new_apartment_gross_m2 = 104,
    new_building_estimated_value_tl = 16500000,
    value_increase_tl = 6500000,
    value_increase_percent = 65.0,
    property_lat = 40.9483,
    property_lng = 29.1303,
    tkgm_cadastre = null
  } = urban;

  const shareOptions = [
    { label: "%40 MÜTEAHHİT", ratio: 0.40 },
    { label: "%45 MÜTEAHHİT", ratio: 0.45 },
    { label: "%50 MÜTEAHHİT (ORTALAMA)", ratio: 0.50 },
    { label: "%55 MÜTEAHHİT", ratio: 0.55 },
    { label: "%60 MÜTEAHHİT", ratio: 0.60 },
  ];

  return (
    <ReportPaywall
      reportTitle="Kentsel Dönüşüm Raporu"
      reportPrice={399}
      onUnlock={() => setUnlocked(true)}
    >
      <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
        
        {/* Header section */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b border-[#E5E7EB] pb-4">
          <div>
            <h3 className="text-2xl font-extrabold text-[#111827] uppercase mt-1 font-display tracking-tight flex items-center gap-2">
              <Hammer className="w-6 h-6 text-[#111827]" />
              Kentsel Dönüşüm Potansiyeli Raporu
            </h3>
            <p className="text-xs text-slate-600 font-medium flex items-center space-x-1">
              <MapPin className="w-3.5 h-3.5 text-[#047857]" />
              <span>{district} / {neighborhood} (Ada: {ada_no} / Parsel: {parsel_no}) — {building_age} Yıllık Bina</span>
            </p>
          </div>

          <button className="light-btn px-5 py-3 rounded-xl text-xs font-extrabold uppercase tracking-wider flex items-center justify-center space-x-2 shrink-0">
            <Download className="w-4 h-4 text-white" />
            <span>ONAYLI PDF RAPORUNU İNDİR</span>
          </button>
        </div>

        {/* TKGM BİNA ÖZNİTELİK BİLGİ KARTI */}
        <div className="p-5 bg-[#FAF8F5] rounded-2xl border-2 border-[#111827] space-y-3">
          <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-2">
            <div className="flex items-center space-x-2 text-xs font-extrabold text-[#111827] uppercase">
              <FileText className="w-4 h-4 text-[#047857]" />
              <span>TKGM RESMİ BİNA VE ARSA ÖZNİTELİK VERİSİ</span>
            </div>
            <span className="text-[11px] font-mono font-extrabold text-[#047857] bg-white px-2 py-0.5 border rounded">
              Taşınmaz ID: TKGM_87123901
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-bold font-mono text-[#111827] bg-white p-3 rounded-xl border border-[#E5E7EB]">
            <div>İlçe / Mahalle: <span className="text-[#047857]">{district} / {neighborhood}</span></div>
            <div>Ada / Parsel: <span className="text-[#111827] bg-[#FAF8F5] px-1.5 py-0.5 rounded">{ada_no} / {parsel_no}</span></div>
            <div>Pafta No: <span className="text-[#111827]">210-15-M</span></div>
            <div>Toplam Arsa: <span className="text-[#047857]">2.415,80 m²</span></div>
          </div>

          <div className="text-xs text-slate-700 font-medium">
            <strong>TKGM Taşınmaz Kaydı: </strong>
            <span className="font-bold text-[#111827]">Kargir 5 Katlı Bina ve Arsası (11 Bağımsız Bölüm)</span>
          </div>
        </div>

        {/* HIGH-ZOOM CADASTRAL PARCEL MAP WITH POLYGON BOUNDARY */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-[#111827]">
            <span className="uppercase">TKGM HASSAS KADASTRO VE BİNA PARSEL POLİGONU HARİTASI</span>
            <span className="font-mono text-[#047857]">Ölçek: High-Zoom (18. Seviye)</span>
          </div>

          <div className="h-64 w-full border-2 border-emerald-500 rounded-2xl relative overflow-hidden bg-[#FAF8F5] shadow-inner">
            <LeafletPolygonMap 
              lat={tkgm_cadastre?.precise_lat || property_lat}
              lng={tkgm_cadastre?.precise_lng || property_lng}
              polygonGeoJson={tkgm_cadastre?.polygon_geometry}
              zoom={19}
            />

            <div className="absolute inset-0 pointer-events-none flex items-center justify-center z-20">
              <div className="w-36 h-28 border border-emerald-500 bg-emerald-500/10 rounded-md relative flex items-center justify-center">
                <div className="text-[10px] font-mono font-black text-emerald-950 bg-white/90 px-2 py-0.5 rounded shadow border border-emerald-400 absolute bottom-1 right-1">
                  Ada: {ada_no} / Parsel: {parsel_no}
                </div>
              </div>
            </div>

            <div className="absolute top-2 left-2 z-20 bg-[#111827] text-white px-3 py-1 rounded-lg text-xs font-mono font-bold shadow-md">
              {district} / {neighborhood} (Kentsel Dönüşüm Binası)
            </div>
          </div>
        </div>

        {/* Contractor Share Selector Buttons */}
        <div className="p-4 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-slate-500 font-extrabold uppercase block">
              MAHALLE MÜTEAHHİT PAYLAŞIM ORANI SİMÜLASYONU
            </span>
            <span className="text-xs font-mono font-extrabold text-[#047857]">
              Seçili Oran: %{Math.round(contractor_share_ratio * 100)} Müteahhit / %{Math.round((1 - contractor_share_ratio) * 100)} Arsa Sahibi
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-bold">
            {shareOptions.map((opt) => {
              const isSelected = Math.abs(contractor_share_ratio - opt.ratio) < 0.01;
              return (
                <button
                  key={opt.ratio}
                  onClick={() => onShareChange && onShareChange(opt.ratio)}
                  className={`py-2 px-2.5 rounded-lg border text-center transition-all ${
                    isSelected
                      ? "bg-[#111827] text-white border-[#111827] shadow-sm"
                      : "bg-white text-[#111827] border-[#E5E7EB] hover:border-[#111827]"
                  }`}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Grid: Transformation Values */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          <div className="p-5 bg-white rounded-xl border border-[#E5E7EB] space-y-2">
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Mevcut Durum ({building_age} Yıllık Bina)</span>
            <div className="text-lg font-extrabold text-[#111827] font-mono">{existing_net_m2} m² Net / {existing_gross_m2} m² Brüt</div>
            <span className="text-xs text-slate-500 block">Ada: {ada_no} / Parsel: {parsel_no}</span>
          </div>

          <div className="p-5 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-2">
            <span className="text-[10px] text-[#047857] uppercase font-bold block">Yenilenmiş Sıfır Daire</span>
            <div className="text-lg font-extrabold text-[#047857] font-mono">{new_apartment_net_m2} m² Net / {new_apartment_gross_m2} m² Brüt</div>
            <span className="text-xs text-[#047857] font-bold block">Yeryüzü Statik Deprem Dayanımlı Sıfır Konut</span>
          </div>

          <div className="p-5 bg-[#111827] text-white rounded-xl space-y-2">
            <span className="text-[10px] text-slate-400 uppercase font-bold block">Dönüşüm Sonrası Değeri</span>
            <div className="text-2xl font-extrabold text-white font-mono">{new_building_estimated_value_tl?.toLocaleString('tr-TR')} ₺</div>
            <span className="text-xs text-amber-400 font-extrabold block">
              +%{value_increase_percent} Prim Artışı (+{value_increase_tl?.toLocaleString('tr-TR')} ₺)
            </span>
          </div>

        </div>

      </div>
    </ReportPaywall>
  );
}
