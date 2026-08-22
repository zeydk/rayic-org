"use client";

import React from "react";

interface ValuationDashboardProps {
  valuation: any;
  financials?: any;
  spatial?: any;
}

export default function ValuationDashboard({ valuation, financials, spatial }: ValuationDashboardProps) {
  if (!valuation) return null;

  const {
    base_m2_price,
    estimated_total_price,
    advertised_price,
    price_per_m2_advertised,
    deviation_percent,
    deal_status,
    status_label,
    k_age,
    k_floor,
    k_tcmb,
    data_collection_date,
    inflation_factor,
    base_m2_price_historical,
    yas_bandi,
    sifir_konut_prim_pct,
  } = valuation;

  const monthlyRent = financials?.estimated_monthly_rent || roundEstimatedRent(estimated_total_price);

  function roundEstimatedRent(salePrice: number) {
    // Approx 1/270 payback estimation
    return Math.round(salePrice / 275 / 500) * 500;
  }

  const isOpportunity = deal_status === "firsat";
  const isOverpriced = deal_status === "asiri_fiyatli";

  return (
    <div className="light-card p-6 bg-white border border-[#E5E7EB] my-4 space-y-5">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#E5E7EB]">
        <div>
          <span className="light-badge text-[10px]">DEĞERLEME ÖZETİ</span>
          <h3 className="text-xl font-extrabold text-[#111827] uppercase mt-1 font-display tracking-tight">
            Piyasa Satış &amp; Kira Değerlemesi
          </h3>
        </div>

        {/* Status Badge */}
        <div
          className={`px-4 py-2 rounded-xl text-sm font-extrabold uppercase tracking-wider ${
            isOpportunity
              ? "bg-[#047857] text-white"
              : isOverpriced
              ? "bg-[#C2410C] text-white"
              : "bg-[#111827] text-white"
          }`}
        >
          {status_label}
        </div>
      </div>

      {/* Primary Metrics Layout - Including Rental Value */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        
        {/* Advertised Price */}
        <div className="p-4 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB]">
          <span className="text-[11px] text-slate-500 font-extrabold uppercase block">İlan Satış Fiyatı</span>
          <span className="text-2xl font-extrabold text-[#111827] mt-1 block font-mono">
            {advertised_price.toLocaleString("tr-TR")} ₺
          </span>
          <span className="text-[11px] text-slate-500 font-bold mt-2 block border-t border-[#E5E7EB] pt-1">
            Metrekare: {price_per_m2_advertised.toLocaleString("tr-TR")} ₺/m²
          </span>
        </div>

        {/* Estimated Fair Value */}
        <div className="p-4 bg-white rounded-xl border-2 border-[#111827] shadow-sm">
          <span className="text-[11px] text-[#111827] font-extrabold uppercase block">Tahmini Piyasa Satış Değeri</span>
          <span className="text-2xl font-extrabold text-[#111827] mt-1 block font-mono">
            {estimated_total_price.toLocaleString("tr-TR")} ₺
          </span>
          <span className="text-[11px] text-slate-600 font-bold mt-2 block border-t border-[#E5E7EB] pt-1">
            Konut Rayici (yaş &amp; bölge bazlı): {base_m2_price.toLocaleString("tr-TR")} ₺/m²
          </span>
          {inflation_factor && inflation_factor > 1.001 && base_m2_price_historical > 0 && (
            <span className="text-[10px] text-[#C2410C] font-semibold mt-0.5 block">
              📈 {base_m2_price_historical.toLocaleString("tr-TR")} ₺/m² ({data_collection_date}) × {inflation_factor.toFixed(2)} TCMB KFE enflasyon = bugünkü rayiç
            </span>
          )}
          {typeof sifir_konut_prim_pct === "number" && sifir_konut_prim_pct > 0.5 && (
            <span className="text-[10px] text-[#7C3AED] font-semibold mt-0.5 block">
              🏗️ Konut yaşı: {yas_bandi} — sıfır (yeni) konut, bu yaştaki daireye göre bölgede ~%{sifir_konut_prim_pct.toFixed(0)} primli
            </span>
          )}
        </div>

        {/* Estimated Monthly Rent */}
        <div className="p-4 bg-white rounded-xl border-2 border-[#047857] shadow-sm">
          <span className="text-[11px] text-[#047857] font-extrabold uppercase block">Tahmini Aylık Kira Fiyatı</span>
          <span className="text-2xl font-extrabold text-[#047857] mt-1 block font-mono">
            {monthlyRent.toLocaleString("tr-TR")} ₺ / Ay
          </span>
          <span className="text-[11px] text-slate-600 font-bold mt-2 block border-t border-[#E5E7EB] pt-1">
            Yıllık Kira: {(monthlyRent * 12).toLocaleString("tr-TR")} ₺
          </span>
        </div>

        {/* Deviation % */}
        <div className="p-4 bg-[#FAF8F5] rounded-xl border border-[#E5E7EB]">
          <span className="text-[11px] text-slate-500 font-extrabold uppercase block">Piyasa Fiyat Farkı</span>
          <div className="flex items-baseline space-x-2 mt-1">
            <span className={`text-2xl font-extrabold font-mono ${
              deviation_percent < -10 ? "text-[#047857]" : deviation_percent > 10 ? "text-[#C2410C]" : "text-[#111827]"
            }`}>
              {deviation_percent > 0 ? `+${deviation_percent}` : deviation_percent}%
            </span>
          </div>
          <span className="text-[11px] text-slate-500 font-bold mt-2 block border-t border-[#E5E7EB] pt-1">
            {deviation_percent < 0 ? "Piyasa Altında (Fırsat)" : "Piyasa Üzerinde"}
          </span>
        </div>

      </div>

      {/* Human Readable Price Factors Breakdown */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-bold pt-3 border-t border-[#E5E7EB]">
        <div className="p-2.5 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB] flex justify-between items-center">
          <span className="text-slate-600">Bina Yaşı Etkisi:</span>
          <span className="text-[#111827] font-mono">{k_age}x</span>
        </div>
        <div className="p-2.5 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB] flex justify-between items-center">
          <span className="text-slate-600">Kat Konumu Etkisi:</span>
          <span className="text-[#111827] font-mono">{k_floor}x</span>
        </div>
        <div className="p-2.5 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB] flex justify-between items-center">
          <span className="text-slate-600">Merkez Bankası Endeksi:</span>
          <span className="text-[#111827] font-mono">{k_tcmb}x</span>
        </div>
        <div className="p-2.5 bg-[#FAF8F5] rounded-lg border border-[#E5E7EB] flex justify-between items-center">
          <span className="text-slate-600">Fark / İskonto:</span>
          <span className="text-[#111827] font-mono">{Math.abs(advertised_price - estimated_total_price).toLocaleString("tr-TR")} ₺</span>
        </div>
      </div>

      {/* TKGM DATA BLOCK */}
      {spatial?.tkgm_cadastre && (
        <div className="mt-6 pt-4 border-t border-[#E5E7EB]">
          <h4 className="text-[11px] font-extrabold text-[#047857] uppercase tracking-wider mb-3 flex items-center space-x-1.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            <span>TKGM Resmi Taşınmaz Öznitelikleri</span>
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs font-medium">
            <div className="p-3 bg-white rounded-lg border border-[#E5E7EB]">
              <span className="text-[10px] text-slate-500 block uppercase">İlçe / Mahalle</span>
              <span className="text-[#111827] font-bold block mt-0.5">{spatial.district} / {spatial.neighborhood}</span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-[#E5E7EB]">
              <span className="text-[10px] text-slate-500 block uppercase">Ada / Parsel</span>
              <span className="text-[#111827] font-bold block mt-0.5">{spatial.tkgm_cadastre.ada_no} / {spatial.tkgm_cadastre.parsel_no}</span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-[#E5E7EB]">
              <span className="text-[10px] text-slate-500 block uppercase">Tapu Alanı</span>
              <span className="text-[#111827] font-bold block mt-0.5">{spatial.tkgm_cadastre.tapu_alani || "Bilgi Yok"}</span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-[#E5E7EB]">
              <span className="text-[10px] text-slate-500 block uppercase">Zemin / Nitelik</span>
              <span className="text-[#111827] font-bold block mt-0.5">{spatial.tkgm_cadastre.zemin_tipi || "Ana Taşınmaz"} - {spatial.tkgm_cadastre.nitelik || "Mesken"}</span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-[#E5E7EB]">
              <span className="text-[10px] text-slate-500 block uppercase">Bağımsız Bölüm</span>
              <span className="text-[#111827] font-bold block mt-0.5">Arsa Payı Kullanıldı</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
