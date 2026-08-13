"use client";

import React from "react";
import { X } from "lucide-react";

interface ListingModalProps {
  isOpen: boolean;
  onClose: () => void;
  children?: React.ReactNode;
}

export default function ListingModal({
  isOpen,
  onClose,
  children,
}: ListingModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fadeIn">
      <div className="bg-white border-2 border-[#111827] rounded-3xl max-w-4xl w-full my-8 p-6 sm:p-8 space-y-4 relative shadow-2xl">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-4">
          <div>
            <h3 className="text-xl font-extrabold text-[#111827] font-display">
              Konut Değerleme Sihirbazı
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              Açık adresinizden lokasyon geocoding, Ada/Parsel tespiti ve piyasa değerlemesi yapılır.
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-slate-100 transition-colors text-slate-500 hover:text-[#111827]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="pt-2">
          {children}
        </div>

      </div>
    </div>
  );
}
