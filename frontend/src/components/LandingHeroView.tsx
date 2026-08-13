"use client";

import React from "react";
import { NavMenu } from "./Header";
import { Calculator, Activity, ShieldCheck, Hammer, ArrowRight, Sparkles, GraduationCap, CheckCircle2, ShoppingBag } from "lucide-react";

interface LandingHeroViewProps {
  onNavigate: (menu: NavMenu) => void;
  onOpenWizard: () => void;
}

export default function LandingHeroView({ onNavigate, onOpenWizard }: LandingHeroViewProps) {
  return (
    <div className="space-y-10 py-4 animate-fadeIn">
      
      {/* Architectural Hero Banner */}
      <div className="light-card p-6 sm:p-10 border border-[#E5E7EB] relative overflow-hidden w-full flex flex-col justify-center min-h-[420px]">
        
        {/* Background Video (HTML5) */}
        <video
          src="/hero-bg.mp4"
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover z-0 opacity-90"
        />
        
        {/* High Contrast Text Container */}
        <div className="relative z-10 w-full md:max-w-lg lg:max-w-xl space-y-5 bg-white/50 backdrop-blur-md p-6 sm:p-8 rounded-3xl shadow-2xl border border-white/50">
          
          <div className="inline-flex items-center space-x-2 light-badge text-[11px] bg-[#0F172A] text-white shadow-sm border-none">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span className="font-bold">ONLINE GAYRİMENKUL EKSPERTİZİ</span>
          </div>

          <div className="space-y-3 w-full">
            <h1 className="text-3xl sm:text-4xl lg:text-[42px] font-extrabold text-[#0F172A] tracking-tight font-display leading-[1.4] pb-1">
              Konutunuz Hakkında Bilmeniz Gereken Her Şey
            </h1>
            <p className="text-sm text-slate-800 font-medium leading-relaxed w-full">
              Piyasa rayici, tahmini kira verimi, deprem risk sınıfı, mahalle asayiş skoru ve kentsel dönüşüm primini anında analiz edin.
            </p>
          </div>

          <div className="pt-1 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <button
              onClick={onOpenWizard}
              className="px-6 py-3.5 rounded-xl text-xs font-extrabold tracking-wider uppercase flex items-center justify-center space-x-3 shadow-lg shadow-blue-900/20 bg-[#0F172A] hover:bg-[#1E293B] text-white transition-all transform hover:scale-[1.02]"
            >
              <Calculator className="w-4 h-4 text-sky-400" />
              <span>ÜCRETSİZ KONUT DEĞERİNİ HESAPLA</span>
            </button>
          </div>

        </div>
      </div>

      {/* 4 Report Products Header */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="light-badge text-[10px]">TEMATİK RAPORLAR KATALOĞU</span>
            <h2 className="text-2xl font-extrabold text-[#111827] font-display mt-1">
              Gayrimenkul Analiz ve Tematik Raporlar
            </h2>
          </div>
          
          <div className="px-3 py-1.5 bg-[#FAF8F5] border border-[#E5E7EB] rounded-xl text-xs font-bold text-[#047857]">
            Tekil Rapor: <strong>399 ₺</strong> | Tam Paket: <strong>999 ₺</strong>
          </div>
        </div>

        {/* Action Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Card 1: Deprem Risk Raporu */}
          <div className="light-card p-6 bg-white border border-[#E5E7EB] hover:border-[#111827] transition-all flex flex-col justify-between space-y-4 group">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-[#FAF8F5] border border-[#E5E7EB] flex items-center justify-center group-hover:bg-[#111827] group-hover:text-white transition-colors">
                <Activity className="w-5 h-5 text-[#111827] group-hover:text-white" />
              </div>
              <span className="text-[10px] font-extrabold text-[#047857] uppercase tracking-wider block">FİYAT: 399 ₺</span>
              <h3 className="text-lg font-extrabold text-[#111827]">
                Deprem Risk Raporu
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Konutunuz deprem riski altında mı? Beklenen büyük depremden nasıl etkilenir ve zemin ne kadar sağlam? Hemen test edin.
              </p>
            </div>

            <button
              onClick={() => onNavigate("earthquake")}
              className="w-full py-2.5 px-3 rounded-xl bg-[#111827] hover:bg-[#047857] text-white text-xs font-bold flex items-center justify-center space-x-2 transition-colors shrink-0"
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              <span>Raporu Satın Al (399 ₺)</span>
            </button>
          </div>

          {/* Card 2: Suç ve Güvenlik Raporu */}
          <div className="light-card p-6 bg-white border border-[#E5E7EB] hover:border-[#111827] transition-all flex flex-col justify-between space-y-4 group">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-[#FAF8F5] border border-[#E5E7EB] flex items-center justify-center group-hover:bg-[#111827] group-hover:text-white transition-colors">
                <ShieldCheck className="w-5 h-5 text-[#111827] group-hover:text-white" />
              </div>
              <span className="text-[10px] font-extrabold text-[#047857] uppercase tracking-wider block">FİYAT: 399 ₺</span>
              <h3 className="text-lg font-extrabold text-[#111827]">
                Suç ve Güvenlik Raporu
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Mahalleniz gerçekten güvenli mi? Geceleri dışarı çıkmadan önce bölgenizin asayiş ve suç istatistiklerini detaylıca keşfedin.
              </p>
            </div>

            <button
              onClick={() => onNavigate("safety")}
              className="w-full py-2.5 px-3 rounded-xl bg-[#111827] hover:bg-[#047857] text-white text-xs font-bold flex items-center justify-center space-x-2 transition-colors shrink-0"
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              <span>Raporu Satın Al (399 ₺)</span>
            </button>
          </div>

          {/* Card 3: Eğitim Kalitesi Raporu */}
          <div className="light-card p-6 bg-white border border-[#E5E7EB] hover:border-[#111827] transition-all flex flex-col justify-between space-y-4 group">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-[#FAF8F5] border border-[#E5E7EB] flex items-center justify-center group-hover:bg-[#111827] group-hover:text-white transition-colors">
                <GraduationCap className="w-5 h-5 text-[#111827] group-hover:text-white" />
              </div>
              <span className="text-[10px] font-extrabold text-[#047857] uppercase tracking-wider block">FİYAT: 399 ₺</span>
              <h3 className="text-lg font-extrabold text-[#111827]">
                Eğitim Kalitesi Raporu
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Çocuğunuz için en iyi eğitim ortamı bu bölgede mi? Çevredeki okulların başarı sıralamalarını ve eğitim standartlarını öğrenin.
              </p>
            </div>

            <button
              onClick={() => onNavigate("education")}
              className="w-full py-2.5 px-3 rounded-xl bg-[#111827] hover:bg-[#047857] text-white text-xs font-bold flex items-center justify-center space-x-2 transition-colors shrink-0"
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              <span>Raporu Satın Al (399 ₺)</span>
            </button>
          </div>

          {/* Card 4: Kentsel Dönüşüm Raporu */}
          <div className="light-card p-6 bg-white border border-[#E5E7EB] hover:border-[#111827] transition-all flex flex-col justify-between space-y-4 group">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-[#FAF8F5] border border-[#E5E7EB] flex items-center justify-center group-hover:bg-[#111827] group-hover:text-white transition-colors">
                <Hammer className="w-5 h-5 text-[#111827] group-hover:text-white" />
              </div>
              <span className="text-[10px] font-extrabold text-[#047857] uppercase tracking-wider block">FİYAT: 399 ₺</span>
              <h3 className="text-lg font-extrabold text-[#111827]">
                Kentsel Dönüşüm Raporu
              </h3>
              <p className="text-xs text-slate-600 font-medium leading-relaxed">
                Eviniz kentsel dönüşüme girerse size ne kadar kazandırır? Yeni dairenizin potansiyel yatırım değerini saniyeler içinde hesaplayın.
              </p>
            </div>

            <button
              onClick={() => onNavigate("urban")}
              className="w-full py-2.5 px-3 rounded-xl bg-[#111827] hover:bg-[#047857] text-white text-xs font-bold flex items-center justify-center space-x-2 transition-colors shrink-0"
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              <span>Raporu Satın Al (399 ₺)</span>
            </button>
          </div>

        </div>
      </div>

      {/* FULL PACKAGE PROMO BANNER */}
      <div className="p-8 bg-[#111827] text-white rounded-2xl border-2 border-black flex flex-col md:flex-row items-center justify-between gap-6 shadow-xl w-full">
        <div className="space-y-3 w-full">
          <div className="inline-flex items-center space-x-2 bg-amber-400 text-[#111827] px-3 py-1 rounded-md text-xs font-black uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4 text-[#111827]" />
            <span>EN POPÜLER: KAPSAMLI GAYRİMENKUL DEĞERLEME TAM PAKETİ</span>
          </div>

          <h3 className="text-2xl sm:text-3xl font-extrabold font-display text-white w-full">
            Tüm 4 Tematik Rapor + Onaylı İndirilebilir PDF Raporu
          </h3>
          <p className="text-xs sm:text-sm text-slate-200 font-medium leading-relaxed w-full">
            Deprem Risk, Güvenlik, Eğitim ve Dönüşüm raporlarının tümünü tek bir paket halinde indirimli olarak satın alın.
          </p>
        </div>

        <div className="text-center md:text-right shrink-0 space-y-3">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 line-through block font-mono font-bold">1.596 ₺</span>
            <span className="text-4xl font-extrabold text-white font-mono block tracking-tight">999 ₺</span>
            <span className="text-[11px] text-amber-400 font-black uppercase tracking-widest block bg-white/10 px-2.5 py-1 rounded-md">
              %37 İNDİRİMLİ TAM PAKET
            </span>
          </div>

          <button
            onClick={onOpenWizard}
            className="w-full sm:w-auto px-6 py-3.5 bg-[#047857] hover:bg-[#065F46] text-white rounded-xl text-xs font-extrabold uppercase tracking-wider transition-all shadow-lg flex items-center justify-center space-x-2"
          >
            <ShoppingBag className="w-4 h-4 text-white" />
            <span>TAM PAKETİ SATIN AL (999 ₺)</span>
          </button>
        </div>
      </div>

    </div>
  );
}
