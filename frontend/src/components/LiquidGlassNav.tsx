"use client";

import React from "react";
import { Wand2, Landmark, Hammer, MapPin, FileText, Sparkles } from "lucide-react";

export type NavTab = "analysis" | "tcmb" | "urban" | "spatial" | "report";

interface LiquidGlassNavProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  hasData: boolean;
}

export default function LiquidGlassNav({ activeTab, onTabChange, hasData }: LiquidGlassNavProps) {
  const navItems = [
    { id: "analysis" as NavTab, label: "Değerleme & İlan", icon: Wand2, badge: null },
    { id: "tcmb" as NavTab, label: "TCMB KFE Endeksi", icon: Landmark, badge: "Makro" },
    { id: "urban" as NavTab, label: "Kentsel Dönüşüm", icon: Hammer, badge: null },
    { id: "spatial" as NavTab, label: "Mekânsal GIS & POI", icon: MapPin, badge: "1 km" },
    { id: "report" as NavTab, label: "Check-Up PDF", icon: FileText, badge: "İndir" },
  ];

  return (
    <nav className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 max-w-xl w-[92%] sm:w-auto">
      {/* Liquid Glass Container */}
      <div className="bg-[#0B101D]/75 backdrop-blur-2xl border border-white/10 shadow-[0_16px_40px_rgba(0,0,0,0.6)] rounded-full p-1.5 flex items-center justify-between sm:justify-center space-x-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`relative px-3.5 py-2 rounded-full text-xs font-semibold transition-all duration-300 flex items-center space-x-2 shrink-0 ${
                isActive
                  ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-white" : "text-slate-400"}`} />
              <span className="hidden sm:inline">{item.label}</span>
              {item.badge && !isActive && (
                <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 hidden md:inline">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
