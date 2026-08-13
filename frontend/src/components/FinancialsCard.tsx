"use client";

import React from "react";

interface FinancialsCardProps {
  financials: any;
}

export default function FinancialsCard({ financials }: FinancialsCardProps) {
  if (!financials) return null;

  const {
    estimated_monthly_rent,
    annual_gross_rent,
    gross_yield_percent,
    net_yield_percent,
    amortization_years,
    amortization_months,
    investment_rating,
    benchmark_comparison,
  } = financials;

  return (
    <div className="light-card p-6 bg-white border border-[#E5E7EB] my-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-[#E5E7EB] mb-4">
        <div>
          <span className="light-badge text-[10px]">KİRA VE YATIRIM GETİRİSİ</span>
          <h3 className="text-xl font-extrabold text-[#111827] uppercase mt-1 font-display tracking-tight">
            Kira Getirisi ve Amortisman Süresi
          </h3>
        </div>

        <div className="px-3 py-1.5 bg-[#FAF8F5] border border-[#E5E7EB] rounded-xl text-xs font-extrabold text-[#111827] uppercase">
          {investment_rating}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 font-bold">
        
        <div className="p-3 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB]">
          <span className="text-[10px] text-slate-500 uppercase block">Tahmini Aylık Kira</span>
          <span className="text-xl font-mono font-extrabold text-[#111827] mt-1 block">
            {estimated_monthly_rent.toLocaleString("tr-TR")} ₺ / Ay
          </span>
          <span className="text-[10px] text-slate-500 font-mono block mt-1">
            Yıllık Toplam: {annual_gross_rent.toLocaleString("tr-TR")} ₺
          </span>
        </div>

        <div className="p-3 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB]">
          <span className="text-[10px] text-slate-500 uppercase block">Yıllık Kira Getiri Oranı</span>
          <span className="text-xl font-mono font-extrabold text-[#111827] mt-1 block">
            %{gross_yield_percent}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block mt-1">
            Net Verim: %{net_yield_percent}
          </span>
        </div>

        <div className="p-3 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB]">
          <span className="text-[10px] text-slate-500 uppercase block">Geri Dönüş (Amortisman)</span>
          <span className="text-xl font-mono font-extrabold text-[#111827] mt-1 block">
            {amortization_years} Yıl
          </span>
          <span className="text-[10px] text-slate-500 font-mono block mt-1">
            Toplam: {amortization_months} Ay
          </span>
        </div>

        <div className="p-3 bg-white rounded-xl border border-[#E5E7EB]">
          <span className="text-[10px] text-slate-500 uppercase block">Bölge Karşılaştırması</span>
          <div className="text-xs space-y-1 mt-1 font-mono">
            <div className="flex justify-between">
              <span>İstanbul Ortalaması:</span>
              <span>19.5 Yıl</span>
            </div>
            <div className="flex justify-between font-extrabold text-[#111827]">
              <span>İlçe Ortalaması:</span>
              <span>{benchmark_comparison?.district_average_years || 18.2} Yıl</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
