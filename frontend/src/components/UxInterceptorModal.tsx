"use client";

import React, { useState, useEffect } from "react";

interface UxInterceptorProps {
  parsedData: any;
  onUpdate: (updated: any) => void;
}

export default function UxInterceptorModal({ parsedData, onUpdate }: UxInterceptorProps) {
  const [district, setDistrict] = useState(parsedData?.district || "Kadıköy");
  const [neighborhood, setNeighborhood] = useState(parsedData?.neighborhood || "Caddebostan");
  const [price, setPrice] = useState<number>(parsedData?.price || 12500000);
  const [netM2, setNetM2] = useState<number>(parsedData?.net_m2 || 95);
  const [buildingAge, setBuildingAge] = useState<number>(parsedData?.building_age ?? 5);
  const [floorCategory, setFloorCategory] = useState<string>(parsedData?.floor_category || "ara_kat");
  const [landNum, setLandNum] = useState<number>(parsedData?.land_share_num || 15);
  const [landDen, setLandDen] = useState<number>(parsedData?.land_share_den || 240);

  useEffect(() => {
    if (parsedData) {
      if (parsedData.district) setDistrict(parsedData.district);
      if (parsedData.neighborhood) setNeighborhood(parsedData.neighborhood);
      if (parsedData.price) setPrice(parsedData.price);
      if (parsedData.net_m2) setNetM2(parsedData.net_m2);
      if (parsedData.building_age !== undefined && parsedData.building_age !== null) setBuildingAge(parsedData.building_age);
      if (parsedData.floor_category) setFloorCategory(parsedData.floor_category);
      if (parsedData.land_share_num) setLandNum(parsedData.land_share_num);
      if (parsedData.land_share_den) setLandDen(parsedData.land_share_den);
    }
  }, [parsedData]);

  const handleFieldChange = (field: string, val: any) => {
    const updated = {
      ...parsedData,
      district,
      neighborhood,
      price,
      net_m2: netM2,
      building_age: buildingAge,
      floor_category: floorCategory,
      land_share_num: landNum,
      land_share_den: landDen,
      [field]: val
    };
    onUpdate(updated);
  };

  return (
    <div className="light-card p-5 bg-white border border-[#E5E7EB] my-4">
      <div className="flex items-center justify-between mb-3 border-b border-[#E5E7EB] pb-2">
        <div className="flex items-center space-x-2">
          <span className="light-badge text-[9px]">UX INTERCEPTOR</span>
          <h3 className="text-sm font-extrabold text-[#111827] uppercase font-display">
            PARAMETRE DÜZENLEME & EKSİK VERİ TAMAMLAMA
          </h3>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2.5 text-xs font-bold">
        
        <div>
          <label className="text-slate-500 block mb-1 uppercase text-[10px]">İlçe</label>
          <select
            value={district}
            onChange={(e) => {
              setDistrict(e.target.value);
              handleFieldChange("district", e.target.value);
            }}
            className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-lg p-2 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
          >
            <option value="Kadıköy">Kadıköy</option>
            <option value="Maltepe">Maltepe</option>
            <option value="Beşiktaş">Beşiktaş</option>
            <option value="Şişli">Şişli</option>
            <option value="Üsküdar">Üsküdar</option>
          </select>
        </div>

        <div>
          <label className="text-slate-500 block mb-1 uppercase text-[10px]">Mahalle</label>
          <select
            value={neighborhood}
            onChange={(e) => {
              setNeighborhood(e.target.value);
              handleFieldChange("neighborhood", e.target.value);
            }}
            className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-lg p-2 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
          >
            {district === "Kadıköy" && (
              <>
                <option value="Caddebostan">Caddebostan</option>
                <option value="Suadiye">Suadiye</option>
                <option value="Caferağa">Caferağa (Moda)</option>
                <option value="Fenerbahçe">Fenerbahçe</option>
                <option value="Göztepe">Göztepe</option>
                <option value="Bostancı">Bostancı</option>
              </>
            )}
            {district === "Maltepe" && (
              <>
                <option value="Küçükyalı">Küçükyalı</option>
                <option value="Yalı">Yalı Mahallesi</option>
                <option value="Altıntepe">Altıntepe</option>
                <option value="İdealtepe">İdealtepe</option>
              </>
            )}
            {district === "Beşiktaş" && (
              <>
                <option value="Bebek">Bebek</option>
                <option value="Etiler">Etiler</option>
                <option value="Levent">Levent</option>
                <option value="Akatlar">Akatlar</option>
              </>
            )}
            {district === "Şişli" && (
              <>
                <option value="Nişantaşı">Nişantaşı</option>
                <option value="Teşvikiye">Teşvikiye</option>
                <option value="Bomonti">Bomonti</option>
              </>
            )}
            {district === "Üsküdar" && (
              <>
                <option value="Kuzguncuk">Kuzguncuk</option>
                <option value="Çengelköy">Çengelköy</option>
                <option value="Kandilli">Kandilli</option>
              </>
            )}
          </select>
        </div>

        <div>
          <label className="text-slate-500 block mb-1 uppercase text-[10px]">Fiyat (TL)</label>
          <input
            type="number"
            value={price}
            onChange={(e) => {
              const val = Number(e.target.value);
              setPrice(val);
              handleFieldChange("price", val);
            }}
            className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-lg p-2 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
          />
        </div>

        <div>
          <label className="text-slate-500 block mb-1 uppercase text-[10px]">Net m²</label>
          <input
            type="number"
            value={netM2}
            onChange={(e) => {
              const val = Number(e.target.value);
              setNetM2(val);
              handleFieldChange("net_m2", val);
            }}
            className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-lg p-2 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
          />
        </div>

        <div>
          <label className="text-slate-500 block mb-1 uppercase text-[10px]">Yaş</label>
          <input
            type="number"
            value={buildingAge}
            onChange={(e) => {
              const val = Number(e.target.value);
              setBuildingAge(val);
              handleFieldChange("building_age", val);
            }}
            className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-lg p-2 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
          />
        </div>

        <div>
          <label className="text-slate-500 block mb-1 uppercase text-[10px]">Kat</label>
          <select
            value={floorCategory}
            onChange={(e) => {
              setFloorCategory(e.target.value);
              handleFieldChange("floor_category", e.target.value);
            }}
            className="w-full bg-[#FAF8F5] border border-[#D1D5DB] rounded-lg p-2 text-[#111827] font-bold focus:outline-none focus:border-[#111827]"
          >
            <option value="ara_kat">Ara Kat (+%10)</option>
            <option value="giris">Giriş / Zemin (-%10)</option>
            <option value="bodrum">Bodrum Kat (-%15)</option>
            <option value="en_ust">En Üst (%0)</option>
          </select>
        </div>

        <div>
          <label className="text-slate-500 block mb-1 uppercase text-[10px]">Arsa Payı</label>
          <div className="flex items-center space-x-1">
            <input
              type="number"
              value={landNum}
              onChange={(e) => {
                const val = Number(e.target.value);
                setLandNum(val);
                handleFieldChange("land_share_num", val);
              }}
              className="w-1/2 bg-[#FAF8F5] border border-[#D1D5DB] rounded-lg p-2 text-[#111827] text-center font-bold"
            />
            <span className="font-extrabold text-[#111827]">/</span>
            <input
              type="number"
              value={landDen}
              onChange={(e) => {
                const val = Number(e.target.value);
                setLandDen(val);
                handleFieldChange("land_share_den", val);
              }}
              className="w-1/2 bg-[#FAF8F5] border border-[#D1D5DB] rounded-lg p-2 text-[#111827] text-center font-bold"
            />
          </div>
        </div>

      </div>
    </div>
  );
}
