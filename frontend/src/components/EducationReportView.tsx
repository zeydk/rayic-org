"use client";

import React, { useState } from "react";
import { GraduationCap, School, Award, Users, BookOpen, Download, MapPin, CheckCircle2 } from "lucide-react";
import ReportPaywall from "./ReportPaywall";

interface EducationReportViewProps {
  data?: any;
  spatial?: any;
  onOpenParser?: () => void;
}

export default function EducationReportView({ data, spatial, onOpenParser }: EducationReportViewProps) {
  const [unlocked, setUnlocked] = useState(false);
  const reportData = data || spatial;

  if (!reportData) {
    return (
      <div className="p-12 bg-white border border-[#E5E7EB] rounded-2xl text-center space-y-4 my-6">
        <GraduationCap className="w-12 h-12 text-[#111827] mx-auto animate-pulse" />
        <h3 className="text-xl font-extrabold text-[#111827] font-display">
          Eğitim Kalitesi Raporu İçin Taşınmaz Seçin
        </h3>
        <p className="text-xs text-slate-600 max-w-md mx-auto">
          1.5 km etki alanındaki devlet okulları, MEB LGS/YKS başarı puanları ve sınıf mevcutlarını inceleyin.
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
    education_report = {
      education_score: 95,
      education_grade: "A+ (Mükemmel Okul Havzası)",
      total_schools_15km: 14,
      top_rated_schools: [
        { name: "Kadıköy Anadolu Lisesi", type: "Lise", distance_meters: 650, lgs_percentile: "%0.45", student_per_classroom: 24, rating_score: 4.9 },
        { name: "Caddebostan İlkokulu", type: "İlkokul", distance_meters: 320, lgs_percentile: null, student_per_classroom: 22, rating_score: 4.8 },
        { name: "Göztepe İhsan Kurşunoğlu Ortaokulu", type: "Ortaokul", distance_meters: 850, lgs_percentile: "%2.10", student_per_classroom: 26, rating_score: 4.7 },
        { name: "Özel Saint-Joseph Fransız Lisesi", type: "Özel Kolej", distance_meters: 1200, lgs_percentile: "%0.80", student_per_classroom: 18, rating_score: 5.0 }
      ],
      education_notes: [
        "1.5 km yarıçap içinde Türkiye'nin en yüksek LGS başarısına sahip 2 köklü lisesi bulunmaktadır.",
        "Devlet okullarında derslik başına düşen ortalama öğrenci sayısı 24 ile Türkiye ortalamasının üzerindedir.",
        "Bölgede ikili öğretim yapılmamakta, tüm okullarda tam gün eğitim uygulanmaktadır."
      ]
    }
  } = reportData;

  return (
    <ReportPaywall
      reportTitle="Eğitim Kalitesi Raporu"
      reportPrice={399}
      onUnlock={() => setUnlocked(true)}
    >
      <div className="space-y-6 my-4 animate-fadeIn">
        
        {/* Header */}
        <div className="light-card p-6 sm:p-8 bg-white border border-[#E5E7EB] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 light-badge text-[10px]">
              <GraduationCap className="w-3.5 h-3.5 text-[#047857]" />
              <span>İHTİSAS RAPORU: 399 ₺</span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#111827] font-display tracking-tight">
              Eğitim Kalitesi Raporu
            </h2>
            <p className="text-xs text-slate-600 font-medium flex items-center space-x-1">
              <MapPin className="w-3.5 h-3.5 text-[#047857]" />
              <span>{district} / {neighborhood} (1.5 km Yarıçap Okul Havzası)</span>
            </p>
          </div>

          <button className="light-btn px-5 py-3 rounded-xl text-xs font-extrabold uppercase tracking-wider flex items-center justify-center space-x-2 shrink-0">
            <Download className="w-4 h-4 text-white" />
            <span>ONAYLI PDF RAPORUNU İNDİR</span>
          </button>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          
          <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2">
            <Award className="w-5 h-5 text-[#111827]" />
            <span className="text-[10px] text-slate-500 font-bold uppercase block">Eğitim Kalite Skoru</span>
            <h4 className="text-xl font-extrabold text-[#111827] font-mono">{education_report.education_score} / 100</h4>
            <span className="text-[11px] text-[#047857] font-bold">{education_report.education_grade}</span>
          </div>

          <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2">
            <School className="w-5 h-5 text-[#111827]" />
            <span className="text-[10px] text-slate-500 font-bold uppercase block">1.5 km Okul Sayısı</span>
            <h4 className="text-xl font-extrabold text-[#111827] font-mono">{education_report.total_schools_15km} Okul</h4>
            <span className="text-[11px] text-slate-600 font-medium">Devlet &amp; Özel Kurumlar</span>
          </div>

          <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2">
            <Users className="w-5 h-5 text-[#111827]" />
            <span className="text-[10px] text-slate-500 font-bold uppercase block">Derslik Başına Öğrenci</span>
            <h4 className="text-xl font-extrabold text-[#111827] font-mono">24 Öğrenci</h4>
            <span className="text-[11px] text-[#047857] font-bold">İdeal Sınıf Kapasitesi</span>
          </div>

          <div className="light-card p-5 bg-white border border-[#E5E7EB] space-y-2">
            <BookOpen className="w-5 h-5 text-[#047857]" />
            <span className="text-[10px] text-slate-500 font-bold uppercase block">Öğretim Tipi</span>
            <h4 className="text-sm font-extrabold text-[#047857] font-mono mt-1">Tam Gün Eğitim</h4>
            <span className="text-[11px] text-slate-600 font-medium">İkili Öğretim Yokdur</span>
          </div>

        </div>

        {/* School List Table */}
        <div className="p-6 bg-white border border-[#E5E7EB] rounded-2xl space-y-4">
          <h4 className="text-sm font-extrabold text-[#111827] uppercase">
            1.5 km Yarıçaptaki Öne Çıkan Okullar ve LGS Başarı Sıralaması
          </h4>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAF8F5] text-slate-500 uppercase font-bold border-b border-[#E5E7EB]">
                <tr>
                  <th className="p-3">Okul Adı</th>
                  <th className="p-3">Tür</th>
                  <th className="p-3">Mesafe</th>
                  <th className="p-3">LGS Başarı Yüzdeliği</th>
                  <th className="p-3">Sınıf Mevcudu</th>
                  <th className="p-3">Değerlendirme</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB] font-medium text-slate-700">
                {(education_report.top_rated_schools || []).map((sch: any, idx: number) => (
                  <tr key={idx} className="hover:bg-[#FAF8F5]/50 transition-colors">
                    <td className="p-3 font-bold text-[#111827]">{sch.name}</td>
                    <td className="p-3">{sch.type}</td>
                    <td className="p-3 font-mono">{sch.distance_meters} m</td>
                    <td className="p-3 font-mono text-[#047857] font-bold">{sch.lgs_percentile || "İlkokul / Derecelendirilmiyor"}</td>
                    <td className="p-3 font-mono">{sch.student_per_classroom} Öğrenci</td>
                    <td className="p-3 font-mono font-bold text-[#111827]">⭐ {sch.rating_score} / 5.0</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </ReportPaywall>
  );
}
