"use client";

import React, { useState } from "react";
import { ShieldCheck, Moon, Sun, Camera, Lock, Download, CheckCircle2 } from "lucide-react";
import ReportPaywall from "./ReportPaywall";

interface SafetyReportViewProps {
  data?: any;
  spatial?: any;
  onOpenParser?: () => void;
}

export default function SafetyReportView({ data, spatial, onOpenParser }: SafetyReportViewProps) {
  const [unlocked, setUnlocked] = useState(false);
  const reportData = data || spatial;

  if (!reportData) {
    return (
      <div className="p-12 bg-white border border-[#E5E7EB] rounded-2xl text-center space-y-4 my-6">
        <ShieldCheck className="w-12 h-12 text-[#111827] mx-auto animate-pulse" />
        <h3 className="text-xl font-extrabold text-[#111827] font-display">
          Suç ve Güvenlik Raporu İçin Taşınmaz Seçin
        </h3>
        <p className="text-xs text-slate-600 max-w-md mx-auto">
          Mahallenizdeki önemli asayiş gelişmeleri hakkında özet bilgi alın, gece yürüyüş güvenliğini ve suç oranlarını inceleyin.
        </p>
        <button
          onClick={onOpenParser}
          className="light-btn px-6 py-3 rounded-xl text-xs font-bold uppercase tracking-wider inline-flex items-center space-x-2"
        >
          <span>Konut Bilgisi Gir</span>
        </button>
      </div>
    );
  }

  const {
    district = "Maltepe",
    neighborhood = "Cumhuriyet",
    safety_report = {
      safety_score: 92,
      safety_grade: "A+ (Çok Güvenli)",
      night_walkability_rating: 4.8,
      street_lighting_score: 95,
      camera_surveillance_index: "MOBESE Destekli Asayiş Bölgesi",
      crime_rate_index: "Düşük Suç Oranı",
      safety_notes: [
        "Mahalle genelinde sokak aydınlatması %95 oranında aktiftir.",
        "Gece yürüyüş güvenliği endeksi 5 üzerinden 4.8 ile çok yüksek seviyededir.",
        "Emniyet kayıtlarına göre ilçe genelinde mala karşı işlenen suç oranı düşüktür."
      ]
    }
  } = reportData;

  return (
    <ReportPaywall
      reportTitle="Suç ve Güvenlik Raporu"
      reportPrice={399}
      onUnlock={() => setUnlocked(true)}
    >
      <div className="space-y-6 my-4 animate-fadeIn">
        
        {/* Header */}
        <div className="light-card p-6 sm:p-8 bg-white border border-[#E5E7EB] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 light-badge text-[10px]">
              <ShieldCheck className="w-3.5 h-3.5 text-[#047857]" />
              <span>İHTİSAS RAPORU: 399 ₺</span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#111827] font-display tracking-tight">
              Suç ve Güvenlik Raporu
            </h2>
            <p className="text-xs text-slate-600 font-medium">
              Mahallenizdeki önemli asayiş gelişmeleri hakkında özet bilgi alın, gece yürüyüş güvenliğini ve suç oranlarını inceleyin.
            </p>
          </div>

          <button className="light-btn px-5 py-3 rounded-xl text-xs font-extrabold uppercase tracking-wider flex items-center justify-center space-x-2 shrink-0">
            <Download className="w-4 h-4 text-white" />
            <span>ONAYLI PDF RAPORUNU İNDİR</span>
          </button>
        </div>

        {/* Grid: 4 Safety Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          
          <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2">
            <Moon className="w-5 h-5 text-[#111827]" />
            <span className="text-[10px] text-slate-500 font-bold uppercase block">Gece Yürüyüş Güvenliği</span>
            <h4 className="text-xl font-extrabold text-[#111827] font-mono">{safety_report.night_walkability_rating} / 5.0</h4>
            <span className="text-[11px] text-[#047857] font-bold">Yüksek Güvenlikli Sokaklar</span>
          </div>

          <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2">
            <Sun className="w-5 h-5 text-[#111827]" />
            <span className="text-[10px] text-slate-500 font-bold uppercase block">Sokak Aydınlatma Oranı</span>
            <h4 className="text-xl font-extrabold text-[#111827] font-mono">%{safety_report.street_lighting_score}</h4>
            <span className="text-[11px] text-[#047857] font-bold">Kesintisiz Aydınlatma</span>
          </div>

          <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2">
            <Camera className="w-5 h-5 text-[#111827]" />
            <span className="text-[10px] text-slate-500 font-bold uppercase block">MOBESE Kamera Kapsamı</span>
            <h4 className="text-sm font-extrabold text-[#111827] font-mono mt-1">Tam Kapsamlı</h4>
            <span className="text-[11px] text-slate-600 font-medium">7/24 İzleme Katmanı</span>
          </div>

          <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2">
            <Lock className="w-5 h-5 text-[#047857]" />
            <span className="text-[10px] text-slate-500 font-bold uppercase block">Asayiş Skor Grubu</span>
            <h4 className="text-sm font-extrabold text-[#047857] font-mono mt-1">{safety_report.safety_grade}</h4>
            <span className="text-[11px] text-slate-600 font-medium">Huzurlu Yerleşim</span>
          </div>

        </div>

        {/* Safety Summary Notes */}
        <div className="p-6 bg-white border border-[#E5E7EB] rounded-2xl space-y-3">
          <h4 className="text-sm font-extrabold text-[#111827] uppercase">
            {district} / {neighborhood} Asayiş Özet Raporu
          </h4>

          <div className="space-y-2">
            {(safety_report.safety_notes || []).map((note: string, idx: number) => (
              <div key={idx} className="flex items-start space-x-2 text-xs font-medium text-slate-700">
                <CheckCircle2 className="w-4 h-4 text-[#047857] shrink-0 mt-0.5" />
                <span>{note}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </ReportPaywall>
  );
}
