"use client";

import React, { useState, useEffect } from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { Landmark } from "lucide-react";

export default function TcmbIndexChart() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/macro/kfe-index")
      .then((res) => res.json())
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((err) => {
        console.error("TCMB KFE fetch error:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="light-card p-6 bg-white border border-[#E5E7EB] animate-pulse">
        <div className="h-6 w-48 bg-slate-200 rounded mb-4"></div>
        <div className="h-64 bg-slate-100 rounded-xl"></div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="light-card p-6 bg-white border border-[#E5E7EB] my-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-[#E5E7EB] mb-5">
        <div>
          <span className="light-badge text-[10px]">TCMB EVDS MAKRO ENDEKS</span>
          <h3 className="text-lg font-extrabold text-[#111827] uppercase mt-1 font-display tracking-tight">
            TCMB KONUT FİYAT ENDEKSİ (KFE) & ALGORİTMA KATKISI
          </h3>
          <p className="text-xs text-slate-500 font-bold mt-0.5">
            Bu endeks verisi K_TCMB çarpanı olarak Otomatik Değerleme Motoruna (P_tahmin) doğrudan etki eder.
          </p>
        </div>

        {/* High Contrast Macro Badges */}
        <div className="flex flex-wrap gap-2 text-xs font-bold">
          <div className="p-2 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB]">
            <span className="text-[10px] text-slate-500 block uppercase">İstanbul KFE</span>
            <span className="font-mono text-sm font-extrabold text-[#111827]">{data.latest_istanbul_index}</span>
          </div>
          <div className="p-2 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB]">
            <span className="text-[10px] text-slate-500 block uppercase">Yıllık Nominal Artış</span>
            <span className="font-mono text-sm font-extrabold text-[#111827]">+{data.nominal_change_yoy}%</span>
          </div>
          <div className="p-2 bg-[#111827] text-white rounded-lg">
            <span className="text-[10px] text-slate-300 block uppercase">Yıllık Reel Prim</span>
            <span className="font-mono text-sm font-extrabold text-emerald-400">+{data.real_change_yoy}%</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64 w-full mt-2 rounded-xl border border-[#E5E7EB] p-2 bg-[#FAF8F5]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data.trend_data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="istanbulLightGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#111827" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#111827" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
            <XAxis dataKey="date" stroke="#6B7280" fontSize={11} tickLine={false} axisLine={false} fontWeight={700} />
            <YAxis stroke="#6B7280" fontSize={11} tickLine={false} axisLine={false} domain={['auto', 'auto']} fontWeight={700} />
            
            <Tooltip
              contentStyle={{
                backgroundColor: "#111827",
                color: "#FAF8F5",
                borderRadius: "8px",
                border: "none",
                fontSize: "12px",
                fontWeight: "700"
              }}
              formatter={(value: any, name: any) => [
                `${value} Puan`,
                name === "istanbul_kfe" ? "İstanbul KFE" : "Türkiye KFE"
              ]}
            />

            <Area
              type="monotone"
              dataKey="istanbul_kfe"
              stroke="#111827"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#istanbulLightGrad)"
              name="istanbul_kfe"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Methodology Note */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-3 border-t border-[#E5E7EB] mt-3 text-xs font-bold text-slate-600">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1">
            <span className="w-3 h-1 bg-[#111827] rounded"></span>
            <span>İstanbul KFE Trendi</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-3 h-1 bg-slate-400 rounded"></span>
            <span>2017=100 Bazlı</span>
          </span>
        </div>
        <span className="text-[11px] font-mono text-slate-500">
          * Kaynak: TCMB Açık Veri Portalı EVDS (Hedonik İndeks)
        </span>
      </div>
    </div>
  );
}
