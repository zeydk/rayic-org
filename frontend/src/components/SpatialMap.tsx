"use client";

import React, { useState, useEffect } from "react";
import { Navigation, Train, Building2, MapPin, CheckCircle2, Trees, ArrowRight, ShieldCheck, Activity, GraduationCap, Hammer } from "lucide-react";
import { NavMenu } from "./Header";

interface SpatialMapProps {
  spatial: any;
  onNavigateToReport?: (menu: NavMenu) => void;
}

export default function SpatialMap({ spatial, onNavigateToReport }: SpatialMapProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!spatial) return null;

  const {
    property_lat,
    property_lng,
    district,
    neighborhood,
    tkgm_cadastre,
    poi_summary,
  } = spatial;

  const cadastre = tkgm_cadastre || {
    ada_no: "2104",
    parsel_no: "15",
    is_auto_matched: true,
    match_accuracy_percent: 99.4,
  };

  return (
    <div className="light-card p-6 bg-white border border-[#E5E7EB] my-4 space-y-6">
      
      {/* Title & Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-[#E5E7EB]">
        <div>
          <span className="light-badge text-[10px]">KENTSEL ALTYAPI VE ÇEVRE ÖZETİ</span>
          <h3 className="text-xl font-extrabold text-[#111827] uppercase mt-1 font-display tracking-tight">
            Konum Analizi, Ulaşım &amp; Yakın Çevre İmkânları
          </h3>
        </div>

        <div className="flex items-center space-x-2 text-xs font-bold text-[#047857] bg-[#FAF8F5] px-3 py-1.5 border border-[#E5E7EB] rounded-xl">
          <MapPin className="w-4 h-4 text-[#047857]" />
          <span>{district} / {neighborhood} (Ada: {cadastre.ada_no} / Parsel: {cadastre.parsel_no})</span>
        </div>
      </div>

      {/* Grid: Map + Infrastructure POI Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Static duotone "keepsake" location map — zoom/pan disabled */}
        <div className="lg:col-span-2 h-80 border-2 border-[#111827] rounded-2xl relative bg-[#0B1F33] overflow-hidden shadow-sm">
          {mounted && (
            <iframe
              title="Taşınmaz Konum Hatırası (Statik)"
              width="100%"
              height="100%"
              frameBorder="0"
              scrolling="no"
              tabIndex={-1}
              aria-hidden="true"
              src={`https://www.openstreetmap.org/export/embed.html?bbox=${property_lng - 0.008}%2C${property_lat - 0.008}%2C${property_lng + 0.008}%2C${property_lat + 0.008}&layer=mapnik&marker=${property_lat}%2C${property_lng}`}
              className="w-full h-full pointer-events-none select-none"
              style={{ filter: "grayscale(100%) sepia(90%) hue-rotate(175deg) saturate(150%) contrast(92%) brightness(1.05)" }}
            />
          )}

          {/* Duotone tint + vignette to complete the keepsake look; also seals the map from interaction */}
          <div className="absolute inset-0 z-10 pointer-events-auto bg-gradient-to-t from-[#0B1F33]/40 via-transparent to-[#0B1F33]/15" />
          <div className="absolute inset-0 z-10 pointer-events-auto shadow-[inset_0_0_60px_rgba(11,31,51,0.5)]" />

          {/* Center location pin (static) */}
          <div className="absolute inset-0 z-20 flex items-center justify-center pointer-events-none">
            <MapPin className="w-9 h-9 text-[#F97316] drop-shadow-[0_2px_4px_rgba(0,0,0,0.6)] -translate-y-2" fill="#F97316" />
          </div>

          <div className="absolute top-2 left-2 z-20 bg-[#111827] text-white px-3 py-1 rounded-lg text-xs font-mono font-bold">
            {district} / {neighborhood} (Taşınmaz Konumu)
          </div>
          <div className="absolute bottom-2 right-2 z-20 bg-[#FAF8F5]/90 text-[#0B1F33] px-2.5 py-1 rounded-md text-[10px] font-extrabold uppercase tracking-wider">
            Statik Konum Hatırası
          </div>
        </div>

        {/* Infrastructure POI Summary Table */}
        <div className="space-y-3 font-bold text-xs flex flex-col justify-between">
          
          <div className="p-4 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB] space-y-2">
            <span className="text-[10px] text-slate-500 block uppercase font-extrabold">1.5 km Yarıçap Altyapı &amp; Yeşil Alan İmkânları</span>
            
            <div className="flex justify-between py-1.5 border-b border-[#E5E7EB]">
              <span className="flex items-center space-x-1.5 text-[#111827]">
                <Trees className="w-4 h-4 text-[#047857]" />
                <span>Parklar &amp; Yeşil Alanlar</span>
              </span>
              <span className="font-mono font-extrabold text-[#047857]">6 Adet Park</span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-[#E5E7EB]">
              <span className="flex items-center space-x-1.5 text-[#111827]">
                <Train className="w-4 h-4 text-[#111827]" />
                <span>Metro İstasyonu</span>
              </span>
              <span className="font-mono font-extrabold">{poi_summary?.metro || 2} Adet</span>
            </div>

            <div className="flex justify-between py-1.5 border-b border-[#E5E7EB]">
              <span className="flex items-center space-x-1.5 text-[#111827]">
                <Navigation className="w-4 h-4 text-[#111827]" />
                <span>Metrobüs / Otobüs Durağı</span>
              </span>
              <span className="font-mono font-extrabold">{poi_summary?.metrobus || 1} Adet</span>
            </div>

            <div className="flex justify-between py-1.5">
              <span className="flex items-center space-x-1.5 text-[#111827]">
                <Building2 className="w-4 h-4 text-[#111827]" />
                <span>Hastane &amp; Sağlık Merkezleri</span>
              </span>
              <span className="font-mono font-extrabold">{poi_summary?.hospital || 3} Adet</span>
            </div>
          </div>

          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-[11px] font-medium leading-relaxed">
            🌿 Bölge kentsel yeşil alan erişilebilirliği yüksek, toplu taşıma akslarına 5-10 dakika yürüme mesafesindedir.
          </div>

        </div>

      </div>

      {/* Prominent CTA Section linking to Specialized Standalone Reports */}
      <div className="pt-4 border-t border-[#E5E7EB] space-y-3">
        <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
          TAŞINMAZA ÖZEL UZMANLIK RAPORLARINI İNCELEYİN VEYA SATIN ALIN:
        </span>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          
          <button
            onClick={() => onNavigateToReport && onNavigateToReport("earthquake")}
            className="p-3.5 bg-[#FAF8F5] hover:bg-[#111827] hover:text-white border border-[#E5E7EB] rounded-xl text-left transition-all flex items-center justify-between group"
          >
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-[#047857] group-hover:text-white" />
              <span className="text-xs font-bold">Deprem Risk Raporu</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-[#047857] group-hover:text-white group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={() => onNavigateToReport && onNavigateToReport("safety")}
            className="p-3.5 bg-[#FAF8F5] hover:bg-[#111827] hover:text-white border border-[#E5E7EB] rounded-xl text-left transition-all flex items-center justify-between group"
          >
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-[#047857] group-hover:text-white" />
              <span className="text-xs font-bold">Suç ve Güvenlik Raporu</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-[#047857] group-hover:text-white group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={() => onNavigateToReport && onNavigateToReport("education")}
            className="p-3.5 bg-[#FAF8F5] hover:bg-[#111827] hover:text-white border border-[#E5E7EB] rounded-xl text-left transition-all flex items-center justify-between group"
          >
            <div className="flex items-center space-x-2">
              <GraduationCap className="w-4 h-4 text-[#047857] group-hover:text-white" />
              <span className="text-xs font-bold">Eğitim Kalitesi Raporu</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-[#047857] group-hover:text-white group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={() => onNavigateToReport && onNavigateToReport("urban")}
            className="p-3.5 bg-[#FAF8F5] hover:bg-[#111827] hover:text-white border border-[#E5E7EB] rounded-xl text-left transition-all flex items-center justify-between group"
          >
            <div className="flex items-center space-x-2">
              <Hammer className="w-4 h-4 text-[#047857] group-hover:text-white" />
              <span className="text-xs font-bold">Kentsel Dönüşüm Raporu</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-[#047857] group-hover:text-white group-hover:translate-x-1 transition-transform" />
          </button>

        </div>
      </div>

    </div>
  );
}
