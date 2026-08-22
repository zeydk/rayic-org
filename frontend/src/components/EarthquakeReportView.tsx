"use client";

import React, { useState } from "react";
import { Activity, ShieldAlert, AlertTriangle, MapPin, Download, Layers, Home, Info } from "lucide-react";
import ReportPaywall from "./ReportPaywall";
import dynamic from "next/dynamic";

const LeafletPolygonMap = dynamic(() => import("./LeafletPolygonMap"), { ssr: false });

interface EarthquakeReportViewProps {
  data?: any;
  spatial?: any;
  onOpenParser?: () => void;
}

// Format a number to at most 2 decimals, stripping floating-point artifacts
// (e.g. 78.05000000000001 -> "78.05", 5 -> "5", 21.9 -> "21.9").
const fmt2 = (n: number): string => {
  if (typeof n !== "number" || !isFinite(n)) return "0";
  return String(Math.round(n * 100) / 100);
};

// Mini gauge component for the cockpit dashboard
const CockpitGauge = ({ label, value, max, colorClass, suffix = "" }: { label: string, value: number, max: number, colorClass: string, suffix?: string }) => {
  const dashArray = 157.08;
  const percentage = Math.max(0, Math.min(value / max, 1));
  const dashOffset = dashArray * (1 - percentage);
  
  return (
    <div className="flex flex-col items-center justify-between p-4 bg-[#FAF8F5] border border-[#E5E7EB] rounded-2xl w-full">
      <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider text-center h-8 leading-tight flex items-end justify-center pb-2">
        {label}
      </span>
      <div className="relative w-24 h-14 overflow-hidden mt-1">
        <svg className="absolute top-0 left-0 w-full h-full" viewBox="0 0 120 70">
          <path
            d="M 10 60 A 50 50 0 0 1 110 60"
            fill="none"
            stroke="#E5E7EB"
            strokeWidth="12"
            strokeLinecap="round"
          />
          <path
            d="M 10 60 A 50 50 0 0 1 110 60"
            fill="none"
            stroke="currentColor"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={dashArray}
            strokeDashoffset={dashOffset}
            className={`${colorClass} transition-all duration-1000 ease-out`}
          />
        </svg>
      </div>
      <div className="font-mono font-black text-xl text-[#111827] mt-1">
        {fmt2(value)}{suffix}
      </div>
    </div>
  );
};

export default function EarthquakeReportView({ data, spatial, onOpenParser }: EarthquakeReportViewProps) {
  const [unlocked, setUnlocked] = useState(false);
  const reportData = data || spatial;

  if (!reportData) {
    return (
      <div className="p-12 bg-white border border-[#E5E7EB] rounded-2xl text-center space-y-4 my-6">
        <Activity className="w-12 h-12 text-[#111827] mx-auto animate-pulse" />
        <h3 className="text-xl font-extrabold text-[#111827] font-display">
          Deprem Risk Raporu İçin Taşınmaz Seçin
        </h3>
        <p className="text-xs text-slate-600 max-w-md mx-auto">
          Mülkünüzün fay hattı mesafesini, zemin risk grubunu ve ivme katsayısını öğrenmek için mülk seçin.
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
    property_lat = 40.95,
    property_lng = 29.1,
    district = "Maltepe",
    neighborhood = "Cumhuriyet",
    tkgm_cadastre,
    ground_risk_class = "Z2 (Orta Sağlam Zemin)",
    pga_earthquake_risk_score = 0.28,
    mmi_estimated = 8.2,
    liquefaction_fs = 0.8,
    district_amplification = 1.3,
    fault_distance_km = 11.4,
    tsunami_risk = "Düşük (Bilinmiyor)",
    tsunami_depth_m = 0,
    tsunami_flood_pct = 0,
    damage_probabilities = {
      hasarsiz: 10,
      hafif: 25,
      orta: 40,
      agir: 20,
      cok_agir: 5
    }
  } = reportData;

  const ada_no = tkgm_cadastre?.ada_no || "2104";
  const parsel_no = tkgm_cadastre?.parsel_no || "15";

  // Helpers for visual gauges
  const getPgaColor = (pga: number) => {
    if (pga < 0.2) return "text-[#047857]"; // Green
    if (pga < 0.35) return "text-amber-500"; // Yellow
    return "text-[#B91C1C]"; // Red
  };

  const getMmiColor = (mmi: number) => {
    if (mmi < 7.0) return "text-[#047857]";
    if (mmi < 8.5) return "text-amber-500";
    return "text-[#B91C1C]";
  };
  
  const getLiqColor = (fs: number) => {
    if (fs > 1.2) return "text-[#047857]";
    if (fs > 1.0) return "text-amber-500";
    return "text-[#B91C1C]";
  };

  let mapZoom = 11;
  if (fault_distance_km > 30) mapZoom = 8;
  else if (fault_distance_km > 15) mapZoom = 9;
  else if (fault_distance_km > 8) mapZoom = 10;
  else if (fault_distance_km > 3) mapZoom = 11;
  
  const heavyDamageProb = damage_probabilities.agir + damage_probabilities.cok_agir;
  let riskVerdict = "DÜŞÜK RİSKLİ";
  let riskColor = "text-[#047857]"; // green
  let riskScore = 20; // out of 100 for gauge

  if (heavyDamageProb > 30) {
    riskVerdict = "ÇOK RİSKLİ";
    riskColor = "text-[#B91C1C]"; // red
    riskScore = 90;
  } else if (heavyDamageProb > 15) {
    riskVerdict = "RİSKLİ";
    riskColor = "text-orange-500";
    riskScore = 70;
  } else if (heavyDamageProb > 5) {
    riskVerdict = "ORTA RİSKLİ";
    riskColor = "text-amber-500";
    riskScore = 45;
  }

  const dashArray = Math.PI * 90;
  const dashOffset = dashArray - (dashArray * riskScore) / 100;

  return (
    <ReportPaywall
      reportTitle="Deprem Risk Raporu"
      reportPrice={399}
      onUnlock={() => setUnlocked(true)}
    >
      <div className="space-y-6 my-4 animate-fadeIn">
        
        {/* Report Header */}
        <div className="light-card p-6 sm:p-8 bg-white border border-[#E5E7EB] flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 light-badge text-[10px]">
              <Activity className="w-3.5 h-3.5 text-[#047857]" />
              <span>İHTİSAS RAPORU: 399 ₺</span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#111827] font-display tracking-tight">
              Deprem Risk Raporu
            </h2>
            <p className="text-xs text-slate-600 font-medium flex items-center space-x-1">
              <MapPin className="w-3.5 h-3.5 text-[#047857]" />
              <span>{district} / {neighborhood} (Ada: {ada_no} / Parsel: {parsel_no})</span>
            </p>
          </div>

          <button className="light-btn px-5 py-3 rounded-xl text-xs font-extrabold uppercase tracking-wider flex items-center justify-center space-x-2 shrink-0">
            <Download className="w-4 h-4 text-white" />
            <span>ONAYLI PDF RAPORUNU İNDİR</span>
          </button>
        </div>

        {/* SECTION 1: Map View (Zoomed into property) */}
        <div className="light-card bg-white border border-[#E5E7EB] rounded-2xl overflow-hidden space-y-0">
          <div className="p-4 border-b border-[#E5E7EB] flex items-center justify-between">
            <h4 className="text-sm font-extrabold text-[#111827] uppercase tracking-wide flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-[#C2410C]" />
              <span>Uydu Görünümü ve Parsel Konumu</span>
            </h4>
            <span className="text-[10px] font-bold text-[#B91C1C] bg-red-50 border border-red-100 px-2 py-1 rounded">
              Fay Hattına Kuşuçuşu: {fault_distance_km} km
            </span>
          </div>
          <div className="h-72 w-full relative bg-[#FAF8F5]">
            <LeafletPolygonMap lat={property_lat} lng={property_lng} zoom={18} showFaultLines={false} />
          </div>
        </div>

        {/* SECTION 2: Cockpit Dashboard */}
        <div className="light-card p-6 sm:p-8 bg-white border border-[#E5E7EB] space-y-8">
          
          <div className="text-center space-y-4">
            <h4 className="text-lg font-extrabold text-[#111827] uppercase tracking-wide">
              Bina Sismik Risk Kararı
            </h4>
            
            {/* MAIN 180-Degree Semi Circle Gauge */}
            <div className="relative w-64 h-36 mx-auto overflow-hidden">
              <svg className="absolute top-0 left-0 w-full h-full" viewBox="0 0 200 110">
                <path
                  d="M 20 100 A 80 80 0 0 1 180 100"
                  fill="none"
                  stroke="#E5E7EB"
                  strokeWidth="20"
                  strokeLinecap="round"
                />
                <path
                  d="M 20 100 A 80 80 0 0 1 180 100"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="20"
                  strokeLinecap="round"
                  strokeDasharray={dashArray}
                  strokeDashoffset={dashOffset}
                  className={`${riskColor} transition-all duration-1000 ease-out`}
                />
              </svg>
              <div className="absolute bottom-0 left-0 w-full text-center pb-2">
                <span className={`text-2xl font-black ${riskColor} font-display tracking-tight`}>{riskVerdict}</span>
              </div>
            </div>
            <p className="text-[11px] font-medium text-slate-500 max-w-md mx-auto">
              İBB Olası Deprem Kayıp Tahminleri algoritmasına göre binanızın yaşı ve yapısal tipine bağlı olarak hesaplanan konsolide risk puanıdır.
            </p>
          </div>

          <hr className="border-[#E5E7EB]" />
          
          {/* COCKPIT SUB-GAUGES */}
          <div className="space-y-4">
            <h4 className="text-xs font-extrabold text-[#111827] uppercase tracking-wide text-center">
              Hasar Olasılıkları Hesabı (7.5 Mw Senaryosu)
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <CockpitGauge
                label="Hasarsız / Hafif"
                value={damage_probabilities.hasarsiz + damage_probabilities.hafif}
                max={100}
                colorClass="text-[#047857]"
                suffix="%"
              />
              <CockpitGauge
                label="Orta Hasar"
                value={damage_probabilities.orta}
                max={100}
                colorClass="text-amber-500"
                suffix="%"
              />
              <CockpitGauge
                label="Ağır Hasar"
                value={damage_probabilities.agir}
                max={100}
                colorClass="text-orange-500"
                suffix="%"
              />
              <CockpitGauge
                label="Çökme Riski"
                value={damage_probabilities.cok_agir}
                max={100}
                colorClass="text-[#B91C1C]"
                suffix="%"
              />
            </div>
          </div>

          {/* Detailed Risk Text (User Facing) */}
          <div className="py-4 space-y-4 text-[14px] text-slate-600 leading-relaxed">
            <p>
              <strong className="text-slate-800 font-medium">{district} ilçesi, {neighborhood} mahallesinde</strong> bulunan bu yapının hasar analizi; Kandilli Rasathanesi ve İstanbul Büyükşehir Belediyesi'nin güncel deprem senaryoları referans alınarak size özel olarak hesaplanmıştır. Bu tablo hazırlanırken sadece mahallenizin genel zemin durumu değil, aynı zamanda belirttiğiniz binanın yaşı ve kat sayısı gibi en hayati faktörler de formüle dahil edilmiştir.
            </p>
            <p>
              Yukarıda gördüğünüz yüzdelik oranlar, olası büyük bir Marmara depreminde (7.5 Mw) binanızın yapısal olarak göstereceği direnci yansıtan mühendislik tahminleridir. Eski yapım yönetmeliklerine tabi olan (özellikle 1999 yılı öncesi inşa edilmiş) ve kat sayısı yüksek olan binalar, depremin sarsıntı gücünü çok daha şiddetli hissettikleri için ağır hasar veya toptan göçme (çökme) riskiyle daha fazla karşı karşıya kalmaktadır. Diğer taraftan, yeni nesil sismik yönetmeliklere (2018 ve sonrası) uygun olarak tasarlanıp denetlenmiş yapılar, bulundukları zemin sınıfı (Z3 veya Z4) zayıf bile olsa, oluşan sarsıntı ve ivmeyi mühendislik kuralları (süneklik) çerçevesinde güvenli bir şekilde sönümleyebilmektedir. Bu yapılar, deprem sırasında can kaybını önleyecek şekilde tasarlanmış olup "hasarsız" veya "hafif hasarlı" olarak ayakta kalma kapasitesini maksimize ederler.
            </p>
            <p>
              Eğer yukarıdaki olasılık analizinde <strong className="text-red-700 font-medium">Çok Ağır (Çökme)</strong> veya <strong className="text-orange-700 font-medium">Ağır Hasar</strong> riskiniz %15'in üzerinde dikkat çekici boyutlardaysa, bu durum yapınızın büyük bir sarsıntı altında can güvenliği standartlarını (Life Safety) sağlamakta zorlanabileceği anlamına gelir. Unutulmamalıdır ki, buradaki oranlar binanız için "kesin bir yıkım kararı" (tahliye kararı) anlamına gelmemekle birlikte, yapınızın risk profilini ortaya koyan oldukça güçlü ve bilimsel bir öngörü niteliğindedir. Bu gibi durumlarda, mülkünüzün değerinden veya kira getirisinden bağımsız olarak, acilen yetkili kurumlara veya lisanslı firmalara karot (performans analiz) testi yaptırarak süreci somutlaştırmanız hayati önem taşır.
            </p>
          </div>

          <hr className="border-[#E5E7EB]" />

          {/* SISMIC METRICS DETAILED VISUALS */}
          <div className="space-y-8">
            <h4 className="text-xs font-extrabold text-[#111827] uppercase tracking-wide text-center">
              Zemin & Sismik Etki Metrikleri
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              
              {/* Olası Şiddet (MMI) Metric */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h5 className="text-[11px] font-extrabold text-[#111827] uppercase">Olası Şiddet (MMI)</h5>
                  <span className="font-mono font-black text-[#B91C1C] text-lg">{mmi_estimated.toFixed(1)}</span>
                </div>
                {/* Horizontal Scale */}
                <div className="relative h-4 w-full bg-slate-200 rounded-full overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 via-amber-400 to-red-600" />
                </div>
                {/* Indicator Marker */}
                <div className="relative w-full">
                  <div 
                    className="absolute top-[-24px] w-4 h-4 bg-[#111827] border-2 border-white rounded-full shadow-md transform -translate-x-1/2" 
                    style={{ left: `${Math.min((mmi_estimated / 12) * 100, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 font-bold mt-1">
                  <span>I</span><span>VI</span><span>IX</span><span>XII</span>
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Modifiye Mercalli Şiddet Ölçeği (MMI), depremin yeryüzünde, insanlar ve yapılar üzerinde yarattığı etkiyi ölçer. Bulunduğunuz parselde 7.5 Mw büyüklüğündeki bir depremin sarsıntı şiddeti <strong>{mmi_estimated.toFixed(1)} MMI</strong> olarak hissedilecektir.
                </p>
              </div>

              {/* Yer İvmesi (PGA) Metric */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h5 className="text-[11px] font-extrabold text-[#111827] uppercase">Pik Yer İvmesi (PGA)</h5>
                  <span className="font-mono font-black text-[#111827] text-lg">{fmt2(pga_earthquake_risk_score)} g</span>
                </div>
                <div className="relative h-4 w-full bg-slate-200 rounded-full overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 via-yellow-400 to-[#991B1B]" />
                </div>
                <div className="relative w-full">
                  <div 
                    className="absolute top-[-24px] w-4 h-4 bg-[#111827] border-2 border-white rounded-full shadow-md transform -translate-x-1/2" 
                    style={{ left: `${Math.min((pga_earthquake_risk_score / 1.0) * 100, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 font-bold mt-1">
                  <span>0.1g</span><span>0.4g</span><span>0.8g</span><span>1.0g+</span>
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Deprem anında zeminin bir saniyedeki maksimum hızlanmasıdır. AFAD Tehlike Haritası ve yerel zemin büyütme katsayınız ({district_amplification}x) dahil edilerek hesaplanan pik yer ivmeniz <strong>{fmt2(pga_earthquake_risk_score)} g</strong> düzeyindedir.
                </p>
              </div>

              {/* Sıvılaşma Güvenliği (FS) Metric */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h5 className="text-[11px] font-extrabold text-[#111827] uppercase">Sıvılaşma Güvenliği (FS)</h5>
                  <span className={`font-mono font-black text-lg ${liquefaction_fs < 1.0 ? 'text-[#B91C1C]' : 'text-[#047857]'}`}>{liquefaction_fs}</span>
                </div>
                <div className="relative h-4 w-full bg-slate-200 rounded-full overflow-hidden flex">
                  <div className="w-[33%] bg-red-500" />
                  <div className="w-[33%] bg-amber-400" />
                  <div className="w-[34%] bg-emerald-500" />
                </div>
                <div className="relative w-full">
                  <div 
                    className="absolute top-[-24px] w-4 h-4 bg-[#111827] border-2 border-white rounded-full shadow-md transform -translate-x-1/2" 
                    style={{ left: `${Math.min((liquefaction_fs / 2.0) * 100, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 font-bold mt-1 px-1">
                  <span className="w-1/3 text-left">Riskli (&lt;1.0)</span>
                  <span className="w-1/3 text-center">Sınırda (~1.2)</span>
                  <span className="w-1/3 text-right">Güvenli (&gt;1.5)</span>
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  TBDY Ek 16B standartlarına göre hesaplanan faktör (FS). Değerin 1.0'ın altında olması, deprem anında yeraltı suyu nedeniyle zeminin taşıma kapasitesini kaybedip "sıvılaşma" (çökme/eğilme) yaşayabileceğini gösterir.
                </p>
              </div>

              {/* Zemin Sınıfı Metric */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h5 className="text-[11px] font-extrabold text-[#111827] uppercase">Mikrobölgeleme Zemin Sınıfı</h5>
                  <span className="font-mono font-black text-[#111827] text-lg">{ground_risk_class.split("(")[0].trim()}</span>
                </div>
                <div className="flex h-4 w-full rounded-full overflow-hidden space-x-1 bg-white">
                  <div className={`flex-1 ${ground_risk_class.includes("Z1") ? 'bg-[#047857]' : 'bg-slate-200'}`} />
                  <div className={`flex-1 ${ground_risk_class.includes("Z2") ? 'bg-emerald-400' : 'bg-slate-200'}`} />
                  <div className={`flex-1 ${ground_risk_class.includes("Z3") ? 'bg-amber-400' : 'bg-slate-200'}`} />
                  <div className={`flex-1 ${ground_risk_class.includes("Z4") ? 'bg-red-500' : 'bg-slate-200'}`} />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 font-bold mt-1 px-2">
                  <span>Z1 (Kaya)</span>
                  <span>Z2 (Sağlam)</span>
                  <span>Z3 (Orta)</span>
                  <span>Z4 (Zayıf)</span>
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Binanız <strong>{ground_risk_class}</strong> grubunda yer almaktadır. Zayıf zeminler (Z3, Z4) deprem dalgalarının genliğini büyüterek (Amplifikasyon) binalara daha şiddetli bir sarsıntı iletir. Bu bölgedeki büyütme katsayısı <strong>{district_amplification}x</strong>'tir.
                </p>
              </div>

              {/* Tsunami Su Basma Riski (MeTHuVA) — full-width bar metric */}
              {tsunami_risk && !tsunami_risk.includes("Bilinmiyor") && (
                <div className="col-span-1 md:col-span-2 space-y-3 mt-2">
                  <div className="flex justify-between items-center">
                    <h5 className="text-[11px] font-extrabold text-[#111827] uppercase">Tsunami Su Basma Riski (MeTHuVA)</h5>
                    <span className={`font-mono font-black text-lg ${tsunami_depth_m >= 3 ? "text-[#B91C1C]" : tsunami_depth_m >= 1 ? "text-amber-500" : "text-[#047857]"}`}>
                      {tsunami_depth_m > 0 ? `${fmt2(tsunami_depth_m)} m` : "Yok"}
                    </span>
                  </div>
                  {/* Gradient depth scale (0 - 8 m) */}
                  <div className="relative h-4 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 via-amber-400 to-[#B91C1C]" />
                  </div>
                  <div className="relative w-full">
                    <div
                      className="absolute top-[-24px] w-4 h-4 bg-[#111827] border-2 border-white rounded-full shadow-md transform -translate-x-1/2"
                      style={{ left: `${Math.min((tsunami_depth_m / 8) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500 font-bold mt-1">
                    <span>Su Yok (0m)</span>
                    <span>Orta (3m)</span>
                    <span>Yüksek (6m)</span>
                    <span>8m+</span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    {tsunami_depth_m >= 1
                      ? <>İBB'nin resmi Tsunami Risk Analizi (MeTHuVA, 2018) modeline göre, olası bir Marmara depremi (Orta Marmara Fayı) kaynaklı tsunamide mahallenizde karada <strong>maksimum ~{fmt2(tsunami_depth_m)} m</strong> su basma derinliği modellenmiştir{tsunami_flood_pct > 0 ? <> (mahalle alanının yaklaşık <strong>%{fmt2(tsunami_flood_pct)}</strong>'i su altında)</> : null}. Afet anında sahil şeridinden hızla uzaklaşılması ve yüksek kesimlere (Tahliye Alanlarına) geçilmesi hayati önem taşır.</>
                      : <>İBB'nin Tsunami Risk Analizi'ne (MeTHuVA, 2018) göre mahalleniz modellenen su baskını alanının dışındadır; olası bir Marmara tsunamisinde doğrudan su basma riski öngörülmemektedir.</>
                    }
                  </p>
                </div>
              )}

            </div>
          </div>
          
        </div>

        {/* Official Advice Box */}
        <div className="p-4 bg-[#FAF8F5] border border-[#E5E7EB] rounded-2xl flex items-start space-x-3">
          <Info className="w-5 h-5 text-[#047857] shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <h5 className="font-extrabold text-[#111827]">Bilimsel Referans ve Yasal Uyarı</h5>
            <p className="text-slate-600 font-medium leading-relaxed">
              Bu rapor, İBB Mikrobölgeleme, AFAD ivme katsayıları ve TBDY Ek 16B sıvılaşma standartları kullanılarak makro ölçekli olasılıksal sismik tehlike analizi sunar. Hasar oranları ampirik kırılganlık eğrilerine dayanır ve yapısal statik bir etüt yerine geçemez. Kesin durum tespiti için Çevre ve Şehircilik Bakanlığı lisanslı firmalardan karotlu bina testi talep ediniz.
            </p>
          </div>
        </div>

      </div>
    </ReportPaywall>
  );
}
