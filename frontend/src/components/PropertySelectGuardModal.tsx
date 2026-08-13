"use client";

import React from "react";
import { AlertCircle, Plus, Building, ArrowRight, X, ShieldAlert } from "lucide-react";

interface PropertySelectGuardProps {
  isOpen: boolean;
  onClose: () => void;
  savedProperties: any[];
  onSelectProperty: (property: any) => void;
  onOpenWizard?: () => void;
  onOpenNewWizard?: () => void;
}

export default function PropertySelectGuardModal({
  isOpen,
  onClose,
  savedProperties = [],
  onSelectProperty,
  onOpenWizard,
  onOpenNewWizard,
}: PropertySelectGuardProps) {
  if (!isOpen) return null;

  const handleOpenWizard = onOpenWizard || onOpenNewWizard;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-white border-2 border-[#111827] rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 relative shadow-2xl">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full hover:bg-slate-100 transition-colors text-slate-500 hover:text-[#111827]"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Warning Icon & Title */}
        <div className="space-y-2 text-center">
          <div className="w-14 h-14 rounded-2xl bg-amber-500/10 text-amber-600 border border-amber-500/20 flex items-center justify-center mx-auto">
            <ShieldAlert className="w-7 h-7" />
          </div>

          <h3 className="text-xl font-extrabold text-[#111827] font-display">
            Tematik Rapor İçin Mülk Seçin
          </h3>
          <p className="text-xs text-slate-600 font-medium leading-relaxed max-w-xs mx-auto">
            Görüntülemek istediğiniz rapor mülk bazlı hazırlanmaktadır. Kayıtlı portföyünüzden bir konut seçin veya yeni bir mülk ekleyin.
          </p>
        </div>

        {/* Saved Properties List */}
        {savedProperties.length > 0 ? (
          <div className="space-y-3">
            <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
              KAYITLI PORTFÖYÜNÜZDEN SEÇİN:
            </span>

            <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
              {savedProperties.map((prop) => (
                <button
                  key={prop.id}
                  onClick={() => onSelectProperty(prop)}
                  className="w-full p-3.5 bg-[#FAF8F5] hover:bg-[#111827] hover:text-white border border-[#E5E7EB] rounded-xl text-left transition-all flex items-center justify-between group"
                >
                  <div className="space-y-0.5">
                    <div className="text-xs font-extrabold">
                      {prop.district} / {prop.neighborhood}
                    </div>
                    <div className="text-[10px] opacity-75 font-mono">
                      Ada: {prop.ada_no || "1420"} / Parsel: {prop.parsel_no || "12"} ({prop.room_count || "3+1"})
                    </div>
                  </div>

                  <ArrowRight className="w-4 h-4 text-[#047857] group-hover:text-white group-hover:translate-x-1 transition-all" />
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {/* Action: Add New Property */}
        <div className="pt-2 border-t border-[#E5E7EB]">
          <button
            onClick={handleOpenWizard}
            className="w-full py-3.5 px-4 rounded-xl bg-[#047857] hover:bg-[#065F46] text-white text-xs font-extrabold uppercase tracking-wider flex items-center justify-center space-x-2 transition-all shadow-md"
          >
            <Plus className="w-4 h-4 text-white" />
            <span>YENİ MÜLK DETAYI EKLE</span>
          </button>
        </div>

      </div>
    </div>
  );
}
