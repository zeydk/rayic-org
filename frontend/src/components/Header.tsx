"use client";

import React from "react";
import { Calculator, Hammer, Plus, ShieldCheck, Activity, User, GraduationCap, MapPin} from "lucide-react";

export type NavMenu = "home" | "valuation" | "earthquake" | "safety" | "education" | "urban" | "guides" | "profile" | "add_property";

interface HeaderProps {
  activeMenu: NavMenu;
  onMenuChange: (menu: NavMenu) => void;
  onOpenParser: () => void;
  savedCount?: number;
}

export default function Header({ activeMenu, onMenuChange, onOpenParser, savedCount = 0 }: HeaderProps) {
  const menuItems: { id: NavMenu; label: string; icon: any }[] = [
    { id: "valuation", label: "Konut Değeri Hesapla", icon: Calculator },
    { id: "earthquake", label: "Deprem Risk Raporu", icon: Activity },
    { id: "safety", label: "Suç Raporu", icon: ShieldCheck },
    { id: "education", label: "Eğitim Raporu", icon: GraduationCap },
    { id: "urban", label: "Kentsel Dönüşüm Raporu", icon: Hammer },
    { id: "profile", label: "Profilim", icon: User },
  ];

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
        {menuItems.map((item) => {
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
      </div>
    </header>
  );
}
