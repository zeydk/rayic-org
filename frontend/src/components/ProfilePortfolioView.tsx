"use client";

import React from "react";
import { User, Building, Trash2, ArrowRight, Bookmark, Plus } from "lucide-react";

export interface SavedProperty {
  id: string;
  userRole?: "buyer" | "seller" | "investor";
  district: string;
  neighborhood: string;
  price?: number;
  net_m2?: number;
  estimatedPrice?: number;
  deviation?: number;
  savedAt?: string;
  date?: string;
  inputData?: any;
  valuationData?: any;
}

interface ProfilePortfolioProps {
  properties?: any[];
  savedProperties?: any[];
  selectedId?: string | null;
  onSelect?: (prop: any) => void;
  onSelectProperty?: (prop: any) => void;
  onRemoveProperty?: (id: string) => void;
  onOpenWizard?: () => void;
  onOpenNewModal?: () => void;
}

export default function ProfilePortfolioView({
  properties,
  savedProperties,
  selectedId,
  onSelect,
  onSelectProperty,
  onRemoveProperty,
  onOpenWizard,
  onOpenNewModal,
}: ProfilePortfolioProps) {
  const propertyList = properties || savedProperties || [];
  const handleSelect = onSelect || onSelectProperty;
  const handleOpenWizard = onOpenWizard || onOpenNewModal;

  return (
    <div className="space-y-6 my-4 animate-fadeIn">
      {/* Profile Header */}
      <div className="light-card p-6 bg-white border border-[#E5E7EB] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-2xl bg-[#111827] text-white flex items-center justify-center font-extrabold text-lg shadow-sm">
            <User className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-[#111827] font-display">
              Profilim ve Kayıtlı Konut Portföyüm
            </h2>
            <p className="text-xs text-slate-500 font-medium">
              Kayıtlı mülklerinizi seçerek tematik raporlarınızı görüntüleyin veya yeni konut ekleyin.
            </p>
          </div>
        </div>

        <button
          onClick={handleOpenWizard}
          className="light-btn px-5 py-3 rounded-xl text-xs font-bold uppercase tracking-wider flex items-center space-x-2 shrink-0"
        >
          <Plus className="w-4 h-4 text-white" />
          <span>Yeni Konut Ekle</span>
        </button>
      </div>

      {/* Property Cards */}
      {propertyList.length === 0 ? (
        <div className="p-12 bg-white border border-[#E5E7EB] rounded-2xl text-center space-y-4">
          <Building className="w-12 h-12 text-[#111827] mx-auto opacity-40" />
          <h3 className="text-lg font-extrabold text-[#111827]">
            Henüz Kayıtlı Mülkünüz Bulunmuyor
          </h3>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            "Yeni Konut Ekle" butonuna tıklayarak ilk taşınmazınızı kaydedin.
          </p>
          <button
            onClick={handleOpenWizard}
            className="light-btn px-6 py-3 rounded-xl text-xs font-bold uppercase tracking-wider inline-flex items-center space-x-2"
          >
            <span>Yeni Konut Ekle</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {propertyList.map((item) => {
            const isSelected = selectedId === item.id;
            return (
              <div
                key={item.id}
                onClick={() => handleSelect && handleSelect(item)}
                className={`light-card p-5 bg-white border rounded-2xl cursor-pointer transition-all space-y-3 relative group ${
                  isSelected ? "border-2 border-[#111827] bg-[#FAF8F5]/80 shadow-md" : "border-[#E5E7EB] hover:border-[#111827]"
                }`}
              >
                {isSelected && (
                  <div className="absolute top-3 right-3 bg-[#111827] text-white text-[10px] font-mono px-2 py-0.5 rounded font-bold">
                    SEÇİLİ MÜLK
                  </div>
                )}

                <div className="flex items-center space-x-2 text-xs font-extrabold text-[#111827]">
                  <Bookmark className="w-4 h-4 text-[#047857]" />
                  <span>{item.district} / {item.neighborhood}</span>
                </div>

                <div className="text-xs space-y-1 text-slate-600 font-medium">
                  <div>Ada: <strong className="text-[#111827]">{item.ada_no || "1420"}</strong> | Parsel: <strong className="text-[#111827]">{item.parsel_no || "12"}</strong></div>
                  <div>Oda Düzeni: <strong className="text-[#111827]">{item.room_count || "3+1"}</strong></div>
                  <div>Kayıt Tarihi: <span className="font-mono text-slate-500">{item.date || "Bugün"}</span></div>
                </div>

                <div className="pt-2 border-t border-[#E5E7EB] flex items-center justify-between">
                  <div className="text-[11px] font-bold text-[#047857] flex items-center group-hover:translate-x-1 transition-transform space-x-1">
                    <span>{item.hasPurchasedReport ? "Bu mülk için rapor mevcut" : "Bu mülk için rapor al"}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                  {onRemoveProperty && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveProperty(item.id);
                      }}
                      className="text-slate-400 hover:text-red-600 transition p-1 rounded-full hover:bg-red-50"
                      title="Mülkü Sil"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
