"use client";

import React, { useState } from "react";
import { Lock, ShoppingBag, CheckCircle2, Sparkles, FileText, ArrowRight, ShieldCheck } from "lucide-react";

interface ReportPaywallProps {
  reportTitle: string;
  reportPrice: number;
  onUnlock: () => void;
  children: React.ReactNode;
}

export default function ReportPaywall({
  reportTitle,
  reportPrice = 399,
  onUnlock,
  children,
}: ReportPaywallProps) {
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  const handleSimulatePurchase = (price: number) => {
    setIsProcessingPayment(true);
    setTimeout(() => {
      setIsProcessingPayment(false);
      setIsUnlocked(true);
      onUnlock();
    }, 600);
  };

  if (isUnlocked) {
    return <>{children}</>;
  }

  return (
    <div className="relative my-4 animate-fadeIn space-y-6">
      
      {/* Blurry Teaser Content Container */}
      <div className="filter blur-[6px] pointer-events-none select-none opacity-40">
        {children}
      </div>

      {/* Paywall Overlay Box */}
      <div className="absolute inset-0 z-30 flex items-start justify-center p-4 pt-12 sm:pt-20">
        <div className="bg-[#111827] text-white border-2 border-black rounded-3xl max-w-xl w-full p-6 sm:p-8 space-y-6 shadow-2xl text-center">
          
          <div className="w-14 h-14 rounded-2xl bg-amber-400 text-[#111827] flex items-center justify-center mx-auto shadow-md">
            <Lock className="w-7 h-7" />
          </div>

          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 bg-white/10 px-3 py-1 rounded-md text-[11px] font-extrabold text-amber-400">
              <Sparkles className="w-3.5 h-3.5" />
              <span>ONAYLI İHTİSAS RAPORU KİLİTLİDİR</span>
            </div>

            <h3 className="text-2xl sm:text-3xl font-extrabold font-display">
              {reportTitle}
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 font-medium max-w-md mx-auto leading-relaxed">
              Tüm detayları görmek, resmi analitiği incelemek ve Onaylı PDF Raporunu indirmek için satın alma yapın.
            </p>
          </div>

          {/* Pricing Action Options */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            
            {/* Option A: Standalone 399 TL */}
            <div className="p-4 bg-white/5 border border-white/10 rounded-2xl space-y-3 flex flex-col justify-between hover:border-amber-400 transition-all text-left">
              <div className="space-y-1">
                <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block">TEKİL İHTİSAS RAPORU</span>
                <div className="text-2xl font-extrabold font-mono text-white">399 ₺</div>
                <p className="text-[11px] text-slate-300 font-medium">Sadece bu rapora ömür boyu erişim ve PDF indirme hakkı.</p>
              </div>

              <button
                onClick={() => handleSimulatePurchase(399)}
                disabled={isProcessingPayment}
                className="w-full py-3 bg-[#047857] hover:bg-[#065F46] text-white rounded-xl text-xs font-extrabold uppercase tracking-wider flex items-center justify-center space-x-1.5 transition-all shadow-md"
              >
                <ShoppingBag className="w-4 h-4 text-white" />
                <span>{isProcessingPayment ? "Ödeme Alınıyor..." : "399 ₺ İLE SATIN AL"}</span>
              </button>
            </div>

            {/* Option B: Full Package 999 TL (%37 Off) */}
            <div className="p-4 bg-amber-400 text-[#111827] rounded-2xl space-y-3 flex flex-col justify-between text-left shadow-lg relative overflow-hidden">
              <div className="space-y-1">
                <span className="text-[10px] font-black uppercase tracking-wider block bg-[#111827] text-amber-400 px-2 py-0.5 rounded w-fit">
                  EN POPÜLER: %37 İNDİRİMLİ
                </span>
                <div className="text-2xl font-extrabold font-mono text-[#111827]">999 ₺ <span className="text-xs line-through opacity-60 font-normal">1.596 ₺</span></div>
                <p className="text-[11px] font-bold leading-tight">Tüm 4 Tematik Rapor (Deprem Risk, Suç, Eğitim, Dönüşüm) Dahil Tam Paket.</p>
              </div>

              <button
                onClick={() => handleSimulatePurchase(999)}
                disabled={isProcessingPayment}
                className="w-full py-3 bg-[#111827] hover:bg-black text-white rounded-xl text-xs font-extrabold uppercase tracking-wider flex items-center justify-center space-x-1.5 transition-all shadow-md"
              >
                <CheckCircle2 className="w-4 h-4 text-amber-400" />
                <span>{isProcessingPayment ? "Ödeme Alınıyor..." : "TAM PAKET AL (999 ₺)"}</span>
              </button>
            </div>

          </div>

          <div className="text-[11px] text-slate-400 font-mono flex items-center justify-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>256-Bit SSL Korumalı Güvenli Ödeme &amp; Anında Dijital Teslimat</span>
          </div>

        </div>
      </div>

    </div>
  );
}
