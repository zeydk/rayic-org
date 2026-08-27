"use client";

import React, { useState } from "react";
import { Calculator, Hammer, Plus, ShieldCheck, Activity, User, GraduationCap, MapPin, FileText, ChevronDown } from "lucide-react";

export type NavMenu = "home" | "valuation" | "earthquake" | "safety" | "education" | "urban" | "guides" | "profile" | "add_property";

interface HeaderProps {
  activeMenu: NavMenu;
  onMenuChange: (menu: NavMenu) => void;
  onOpenParser: () => void;
  savedCount?: number;
}

export default function Header({ activeMenu, onMenuChange, onOpenParser, savedCount = 0 }: HeaderProps) {
  // Üst barda 6 öğe + Mahalle Rehberi sığmıyordu (taşıyordu). Artık ANA
  // öğeler barda, dört tematik RAPOR tek bir açılır menüde toplandı.
  const menuItems: { id: NavMenu; label: string; icon: any }[] = [
    { id: "valuation", label: "Konut Değeri Hesapla", icon: Calculator },
    { id: "profile", label: "Profilim", icon: User },
  ];
  const raporlar: { id: NavMenu; label: string; icon: any }[] = [
    { id: "earthquake", label: "Deprem Risk Raporu", icon: Activity },
    { id: "safety", label: "Suç ve Güvenlik Raporu", icon: ShieldCheck },
    { id: "education", label: "Eğitim Kalitesi Raporu", icon: GraduationCap },
    { id: "urban", label: "Kentsel Dönüşüm Raporu", icon: Hammer },
  ];
  const [raporAcik, setRaporAcik] = useState(false);
  const raporAktif = raporlar.some((r) => r.id === activeMenu);

  return (
    <header className="sticky top-0 z-50 bg-[#FAF8F5]/90 backdrop-blur-md border-b border-[#E5E7EB]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Identity - Clicking Logo goes to Landing Page */}
        <button
          onClick={() => onMenuChange("home")}
          className="flex items-center space-x-2 focus:outline-none group shrink-0"
          title="Anasayfa"
        >
          <img 
            src="/logo.png" 
            alt="Rayiç Logo" 
            className="h-14 w-auto mix-blend-multiply group-hover:scale-105 transition-transform" 
          />
          <span className="font-extrabold text-lg tracking-tight text-[#111827] font-display">
            Rayic.org
          </span>
        </button>

        {/* Top Navigation Bar - Clean 6 Item Layout */}
        <nav className="hidden md:flex items-center space-x-1 overflow-x-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeMenu === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onMenuChange(item.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 whitespace-nowrap border ${
                  isActive
                    ? "bg-[#111827] text-[#FAF8F5] border-[#111827] shadow-sm"
                    : "text-slate-700 border-transparent hover:bg-[#E5E7EB]/50 hover:text-[#111827]"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-[#FAF8F5]" : "text-slate-500"}`} />
                <span>{item.label}</span>
                {item.id === "profile" && savedCount > 0 && (
                  <span className="ml-1 px-1.5 py-0.2 bg-[#047857] text-white text-[10px] rounded-full font-mono">
                    {savedCount}
                  </span>
                )}
              </button>
            );
          })}
          {/* RAPORLAR — dördü tek açılır menüde (üst bar taşmasın) */}
          <div className="relative">
            <button
              onClick={() => setRaporAcik((v) => !v)}
              onBlur={() => setTimeout(() => setRaporAcik(false), 150)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 whitespace-nowrap border ${
                raporAktif
                  ? "bg-[#111827] text-[#FAF8F5] border-[#111827] shadow-sm"
                  : "text-slate-700 border-transparent hover:bg-[#E5E7EB]/50 hover:text-[#111827]"
              }`}
            >
              <FileText className={`w-3.5 h-3.5 ${raporAktif ? "text-[#FAF8F5]" : "text-slate-500"}`} />
              <span>Raporlar</span>
              <ChevronDown className={`w-3 h-3 transition-transform ${raporAcik ? "rotate-180" : ""}`} />
            </button>
            {raporAcik && (
              <div className="absolute right-0 mt-1 w-60 bg-white border border-[#111827] rounded-xl shadow-xl overflow-hidden z-50">
                {raporlar.map((r) => {
                  const RI = r.icon;
                  return (
                    <button
                      key={r.id}
                      onMouseDown={() => { onMenuChange(r.id); setRaporAcik(false); }}
                      className={`w-full text-left px-3 py-2.5 text-xs font-bold flex items-center gap-2 transition-colors ${
                        activeMenu === r.id ? "bg-[#047857] text-white" : "text-[#111827] hover:bg-[#FAF8F5]"
                      }`}
                    >
                      <RI className="w-3.5 h-3.5" />
                      {r.label}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Mahalle Rehberi ayrı bir ROUTE'tur (SEO için sunucuda render edilir),
              SPA sekmesi değil — bu yüzden gerçek link kullanılıyor. */}
          <a
            href="/mahalleler"
            className="px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 whitespace-nowrap border text-slate-700 border-transparent hover:bg-[#E5E7EB]/50 hover:text-[#111827]"
          >
            <MapPin className="w-3.5 h-3.5 text-slate-500" />
            <span>Mahalle Rehberi</span>
          </a>
        </nav>

        {/* Primary Action Button */}
        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={onOpenParser}
            className="light-btn px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 whitespace-nowrap"
          >
            <Plus className="w-3.5 h-3.5 text-[#FAF8F5]" />
            <span>İlan Detayları Gir</span>
          </button>
        </div>

      </div>

      {/* Mobile Navigation */}
      <div className="md:hidden flex overflow-x-auto border-t border-[#E5E7EB] bg-[#FAF8F5] p-2 text-xs space-x-1">
        {[...menuItems, ...raporlar].map((item) => {
          const Icon = item.icon;
          const isActive = activeMenu === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onMenuChange(item.id)}
              className={`px-2.5 py-1.5 rounded-lg font-bold text-[11px] whitespace-nowrap flex items-center space-x-1 ${
                isActive ? "bg-[#111827] text-white" : "text-slate-600"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{item.label}</span>
            </button>
          );
        })}
        {/* Mobilde de rehber erişilebilir olsun */}
        <a href="/mahalleler"
           className="px-2.5 py-1.5 rounded-lg font-bold text-[11px] whitespace-nowrap flex items-center space-x-1 text-slate-600">
          <MapPin className="w-3.5 h-3.5" />
          <span>Mahalle Rehberi</span>
        </a>
      </div>
    </header>
  );
}
