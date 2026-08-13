"use client";

import React, { useState } from "react";
import { Download, Loader2, CheckCircle2 } from "lucide-react";

interface PdfReportButtonProps {
  payloadData: any;
}

export default function PdfReportButton({ payloadData }: PdfReportButtonProps) {
  const [downloading, setDownloading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleDownloadPdf = async () => {
    if (!payloadData) return;
    setDownloading(true);
    setSuccess(false);

    try {
      const response = await fetch("http://localhost:8000/api/v1/report/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payloadData),
      });

      if (!response.ok) {
        throw new Error("PDF generation failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rayic_degerleme_raporu_${payloadData.district || "Kadikoy"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      console.error("PDF Download error:", err);
      alert("PDF Rapor üretilirken sunucu hatası oluştu.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="light-card p-6 bg-white border border-[#E5E7EB] my-4 flex flex-col md:flex-row items-center justify-between gap-6">
      <div>
        <span className="light-badge text-[10px]">GAYRİMENKUL RAPORU</span>
        <h4 className="text-lg font-extrabold text-[#111827] uppercase mt-1 font-display tracking-tight">
          Detaylı Gayrimenkul Değerleme ve Analiz Raporu (PDF)
        </h4>
        <p className="text-xs text-slate-600 font-bold mt-1 max-w-xl">
          Konut piyasa değerlemesi, amortisman süresi, arsa payı güvenliği ve zemin durumunu içeren resmi PDF raporu.
        </p>
      </div>

      <button
        onClick={handleDownloadPdf}
        disabled={downloading}
        className={`light-btn px-6 py-3.5 text-xs font-extrabold uppercase tracking-wider flex items-center space-x-2 shrink-0 ${
          success ? "bg-[#047857]" : ""
        }`}
      >
        {downloading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-white" />
            <span>RAPOR İNDİRİLİYOR...</span>
          </>
        ) : success ? (
          <>
            <CheckCircle2 className="w-4 h-4 text-white" />
            <span>RAPOR İNDİRİLDİ!</span>
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            <span>PDF RAPORU İNDİR</span>
          </>
        )}
      </button>
    </div>
  );
}
