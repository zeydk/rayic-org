"use client";

import React, { useState, useEffect } from "react";
import { MapPin, Layers, Sparkles } from "lucide-react";

interface MapLocationPickerProps {
  district: string;
  neighborhood: string;
  selectedLat: number;
  selectedLng: number;
  adaNo?: string;
  parselNo?: string;
  onLocationSelect?: (lat: number, lng: number) => void;
}

export const DISTRICT_COORDS: Record<string, { lat: number; lng: number }> = {
  // ANADOLU YAKASI
  "Adalar": { lat: 40.8742, lng: 29.1293 },
  "Ataşehir": { lat: 40.9847, lng: 29.1067 },
  "Beykoz": { lat: 41.1325, lng: 29.1008 },
  "Çekmeköy": { lat: 41.0353, lng: 29.1764 },
  "Kadıköy": { lat: 40.9812, lng: 29.0254 },
  "Kartal": { lat: 40.8886, lng: 29.1856 },
  "Maltepe": { lat: 40.9483, lng: 29.1303 },
  "Pendik": { lat: 40.8789, lng: 29.2334 },
  "Sancaktepe": { lat: 41.0025, lng: 29.2361 },
  "Sultanbeyli": { lat: 40.9639, lng: 29.2647 },
  "Şile": { lat: 41.1761, lng: 29.6128 },
  "Tuzla": { lat: 40.8164, lng: 29.3014 },
  "Ümraniye": { lat: 41.0256, lng: 29.0964 },
  "Üsküdar": { lat: 41.0264, lng: 29.0153 },

  // AVRUPA YAKASI
  "Arnavutköy": { lat: 41.1844, lng: 28.7411 },
  "Avcılar": { lat: 40.9797, lng: 28.7217 },
  "Bağcılar": { lat: 41.0336, lng: 28.8578 },
  "Bahçelievler": { lat: 40.9947, lng: 28.8603 },
  "Bakırköy": { lat: 40.9803, lng: 28.8722 },
  "Başakşehir": { lat: 41.0975, lng: 28.8067 },
  "Bayrampaşa": { lat: 41.0353, lng: 28.9117 },
  "Beşiktaş": { lat: 41.0428, lng: 29.0075 },
  "Beylikdüzü": { lat: 40.9908, lng: 28.6497 },
  "Beyoğlu": { lat: 41.0369, lng: 28.9775 },
  "Büyükçekmece": { lat: 41.0208, lng: 28.5817 },
  "Çatalca": { lat: 41.1436, lng: 28.4614 },
  "Esenler": { lat: 41.0489, lng: 28.8906 },
  "Esenyurt": { lat: 41.0342, lng: 28.6806 },
  "Eyüpsultan": { lat: 41.0475, lng: 28.9336 },
  "Fatih": { lat: 41.0186, lng: 28.9497 },
  "Gaziosmanpaşa": { lat: 41.0575, lng: 28.9158 },
  "Güngören": { lat: 41.0189, lng: 28.8778 },
  "Kağıthane": { lat: 41.0806, lng: 28.9778 },
  "Küçükçekmece": { lat: 41.0006, lng: 28.7778 },
  "Sarıyer": { lat: 41.1664, lng: 29.0578 },
  "Silivri": { lat: 41.0744, lng: 28.2478 },
  "Sultangazi": { lat: 41.1047, lng: 28.8686 },
  "Şişli": { lat: 41.0603, lng: 28.9878 },
  "Zeytinburnu": { lat: 40.9903, lng: 28.9039 }
};

export default function MapLocationPicker({
  district,
  neighborhood,
  selectedLat,
  selectedLng,
  adaNo = "1420",
  parselNo = "12",
  onLocationSelect
}: MapLocationPickerProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const lat = selectedLat || DISTRICT_COORDS[district]?.lat || 40.9812;
  const lng = selectedLng || DISTRICT_COORDS[district]?.lng || 29.0254;

  // Calculate tight bounding box for high-zoom 18 precision
  const zoomOffset = 0.0018;
  const bbox = `${lng - zoomOffset}%2C${lat - zoomOffset}%2C${lng + zoomOffset}%2C${lat + zoomOffset}`;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs font-bold text-[#111827]">
        <div className="flex items-center space-x-1.5">
          <MapPin className="w-4 h-4 text-[#047857]" />
          <span>HARİTADAN BİNANIZIN HASSAS KONUMUNU İĞNE İLE DÜZELTİN <span className="text-red-500">*</span></span>
        </div>
        <span className="text-[11px] font-mono text-[#047857] bg-white px-2 py-0.5 border border-[#E5E7EB] rounded-md">
          Hassas Konum: {lat.toFixed(4)}, {lng.toFixed(4)}
        </span>
      </div>

      <div className="h-72 w-full border-2 border-[#111827] rounded-2xl relative overflow-hidden bg-[#FAF8F5] shadow-inner group">
        
        {/* OpenStreetMap High-Zoom View */}
        {mounted && (
          <iframe
            title="Ada Parsel Hassas Konum Haritası"
            width="100%"
            height="100%"
            frameBorder="0"
            src={`https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat}%2C${lng}`}
            className="w-full h-full filter contrast-105"
          />
        )}

        {/* CADASTRAL PARSEL POLYGON BOUNDARY OVERLAY */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center z-10">
          
          {/* Simulated Cadastral Parcel Polygon Box */}
          <div className="w-36 h-28 border-2 border-emerald-500 bg-emerald-500/15 rounded-md relative shadow-lg flex items-center justify-center animate-pulse">
            
            {/* Polygon Corner Anchors */}
            <div className="absolute -top-1 -left-1 w-2.5 h-2.5 bg-emerald-600 rounded-full border border-white"></div>
            <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-600 rounded-full border border-white"></div>
            <div className="absolute -bottom-1 -left-1 w-2.5 h-2.5 bg-emerald-600 rounded-full border border-white"></div>
            <div className="absolute -bottom-1 -right-1 w-2.5 h-2.5 bg-emerald-600 rounded-full border border-white"></div>

            <div className="text-[10px] font-mono font-black text-emerald-950 bg-white/90 px-2 py-0.5 rounded shadow border border-emerald-400">
              Ada: {adaNo} / Parsel: {parselNo}
            </div>
          </div>
        </div>

        {/* Floating Controls Overlay */}
        <div className="absolute top-2 left-2 z-20 bg-[#111827] text-white px-3 py-1.5 rounded-lg text-xs font-mono font-bold shadow-md flex items-center space-x-1.5">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span>{district} / {neighborhood} (Kadastro Parsel Sınırı)</span>
        </div>

        <div className="absolute bottom-2 right-2 z-20 bg-white/95 text-[#111827] px-3 py-1 rounded-lg text-[11px] font-bold border border-[#E5E7EB] shadow">
          🔍 Haritaya Tıklayarak İğneyi Binanıza Yerleştirin
        </div>
      </div>
    </div>
  );
}
