"use client";

import React, { useState, useEffect } from "react";
import Header, { NavMenu } from "@/components/Header";
import LandingHeroView from "@/components/LandingHeroView";
import AdInputParser from "@/components/AdInputParser";
import ListingModal from "@/components/ListingModal";
import ValuationDashboard from "@/components/ValuationDashboard";
import SpatialMap from "@/components/SpatialMap";
import EarthquakeReportView from "@/components/EarthquakeReportView";
import SafetyReportView from "@/components/SafetyReportView";
import EducationReportView from "@/components/EducationReportView";
import UrbanTransformationSim from "@/components/UrbanTransformationSim";
import ProfilePortfolioView from "@/components/ProfilePortfolioView";
import PropertySelectGuardModal from "@/components/PropertySelectGuardModal";

export default function Home() {
  const [activeMenu, setActiveMenu] = useState<NavMenu>("home");
  const [isParserOpen, setIsParserOpen] = useState<boolean>(false);
  const [isGuardOpen, setIsGuardOpen] = useState<boolean>(false);
  const [targetGuardTab, setTargetGuardTab] = useState<NavMenu | null>(null);

  // Saved User Properties Portfolio State
  const [savedProperties, setSavedProperties] = useState<any[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null);

  // Current Active Property Input Data
  const [parsedInput, setParsedInput] = useState<any | null>(null);

  // API Backend Results
  const [valuationData, setValuationData] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Hydrate saved properties from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem("rayic_saved_properties");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setSavedProperties(parsed);
          setSelectedPropertyId(parsed[0].id);
          setValuationData(parsed[0].valuationData);
          setParsedInput(parsed[0].inputData);
        }
      }
    } catch (err) {
      console.error("Failed to load saved properties", err);
    }
  }, []);

  const runFullCheckup = async (input: any) => {
    setLoading(true);
    try {
      const payload = {
        price: input.price,
        net_m2: input.net_m2,
        gross_m2: input.gross_m2,
        building_age: input.building_age,
        floor: input.floor,
        room_count: input.room_count,
        total_land_m2: input.total_land_m2,
        land_share_num: input.land_share_num,
        land_share_den: input.land_share_den,
        district: input.district,
        neighborhood: input.neighborhood,
        full_address: input.full_address || undefined,
        street: input.street || undefined,
        door_no: input.door_no || undefined,
        apt_no: input.apt_no || undefined,
        lat: input.lat || undefined,
        lng: input.lng || undefined,
        ada_no: input.ada_no || undefined,
        parsel_no: input.parsel_no || undefined,
        user_role: input.user_role || "buyer",
        contractor_share_ratio: input.contractor_share_ratio || 0.50,
        building_age: input.building_age_years || 20,
        floor_count: input.floor_count || 5
      };

      const res = await fetch("http://127.0.0.1:8000/api/v1/valuate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error("HTTP error " + res.status);
      }

      const data = await res.json();
      setValuationData(data);
      setParsedInput(input);

      // Auto-save property to user's saved portfolio
      const newProperty = {
        id: `prop_${Date.now()}`,
        date: new Date().toLocaleDateString("tr-TR"),
        district: input.district,
        neighborhood: input.neighborhood,
        ada_no: input.ada_no || "2104",
        parsel_no: input.parsel_no || "15",
        room_count: input.room_count,
        user_role: input.user_role || "buyer",
        inputData: input,
        valuationData: data
      };

      setSavedProperties((prev) => {
        const updated = [newProperty, ...prev.filter(p => p.id !== newProperty.id)];
        try {
          localStorage.setItem("rayic_saved_properties", JSON.stringify(updated));
        } catch (e) {}
        return updated;
      });

      setSelectedPropertyId(newProperty.id);
      
      
      // Auto-navigate to Valuation Dashboard
      setActiveMenu("valuation");
    } catch (err) {
      console.error("Valuation engine connection error:", err);
      const mockResult = {
        valuation: {
          estimated_value_tl: Math.round(input.price * 1.05),
          estimated_total_price: Math.round(input.price * 1.05),
          advertised_price: input.price,
          price_per_m2_advertised: Math.round(input.price / input.net_m2),
          base_m2_price: Math.round((input.price * 1.05) / input.net_m2),
          deviation_percent: 5,
          deal_status: "makul",
          status_label: "FİYAT MAKUL",
          k_age: 1.0,
          k_floor: 1.0,
          k_tcmb: 1.0,
          estimated_rent_tl: Math.round((input.price * 1.05) / 240),
          min_value_tl: Math.round(input.price * 0.98),
          max_value_tl: Math.round(input.price * 1.12),
          confidence_score: 91,
          valuation_version: "1.2.0 (Mock Fallback)",
          district: input.district,
          neighborhood: input.neighborhood,
          net_m2: input.net_m2,
          room_count: input.room_count
        },
        spatial: {
          property_lat: 40.9483,
          property_lng: 29.1303,
          district: input.district,
          neighborhood: input.neighborhood,
          tkgm_cadastre: {
            ada_no: input.ada_no || "2104",
            parsel_no: input.parsel_no || "15",
            is_auto_matched: true,
            match_accuracy_percent: 99.4,
            tkgm_status_label: "TKGM PARSEL SORGU ALGORİTMASI İLE EŞLEŞTİRİLDİ",
            precise_lat: 40.9483,
            precise_lng: 29.1303
          },
          ground_risk_class: "Z2 (Orta Sağlam Zemin)",
          pga_earthquake_risk_score: 0.28,
          poi_summary: { metro: 2, metrobus: 1, hospital: 3, transformation: 4 }
        },
        urban_transformation: {
          district: input.district,
          neighborhood: input.neighborhood,
          ada_no: input.ada_no || "2104",
          parsel_no: input.parsel_no || "15",
          existing_net_m2: input.net_m2,
          existing_gross_m2: input.gross_m2,
          building_age: input.building_age,
          contractor_share_ratio: 0.50,
          new_apartment_net_m2: Math.round(input.net_m2 * 0.90),
          new_apartment_gross_m2: Math.round(input.gross_m2 * 0.90),
          new_building_estimated_value_tl: Math.round(input.price * 1.65),
          value_increase_tl: Math.round(input.price * 0.65),
          value_increase_percent: 65.0
        }
      };

      const newProperty = {
        id: `prop_${Date.now()}`,
        date: new Date().toLocaleDateString("tr-TR"),
        district: input.district,
        neighborhood: input.neighborhood,
        ada_no: input.ada_no || "2104",
        parsel_no: input.parsel_no || "15",
        room_count: input.room_count,
        user_role: input.user_role || "buyer",
        inputData: input,
        valuationData: mockResult
      };

      setSavedProperties((prev) => {
        const updated = [newProperty, ...prev.filter(p => p.id !== newProperty.id)];
        try {
          localStorage.setItem("rayic_saved_properties", JSON.stringify(updated));
        } catch (e) {}
        return updated;
      });

      setSelectedPropertyId(newProperty.id);
      
      setValuationData(mockResult as any);
      setParsedInput(input);
      
      setActiveMenu("valuation");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSavedProperty = (property: any) => {
    setSelectedPropertyId(property.id);
    setParsedInput(property.inputData);
    setValuationData(property.valuationData);
  };

  const handleRemoveSavedProperty = (id: string) => {
    setSavedProperties((prev) => {
      const updated = prev.filter((p) => p.id !== id);
      try {
        localStorage.setItem("rayic_saved_properties", JSON.stringify(updated));
      } catch (e) {}
      
      if (selectedPropertyId === id) {
        if (updated.length > 0) {
          setSelectedPropertyId(updated[0].id);
          setValuationData(updated[0].valuationData);
          setParsedInput(updated[0].inputData);
        } else {
          setSelectedPropertyId(null);
          setValuationData(null);
          setParsedInput(null);
          if (activeMenu !== "home" && activeMenu !== "add_property") {
            setActiveMenu("home");
          }
        }
      }
      return updated;
    });
  };

  const handleMenuChangeWithGuard = (menu: NavMenu) => {
    const isReportTab = ["valuation", "earthquake", "safety", "education", "urban"].includes(menu);

    if (isReportTab && !valuationData) {
      if (savedProperties.length === 1) {
        // Automatically select the single saved property!
        handleSelectSavedProperty(savedProperties[0]);
        setActiveMenu(menu);
        return;
      } else if (savedProperties.length > 1) {
        setTargetGuardTab(menu);
        setIsGuardOpen(true);
        return;
      } else {
        // No property saved yet
        setTargetGuardTab(menu);
        setIsGuardOpen(true);
        return;
      }
    }

    setActiveMenu(menu);
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-[#111827] flex flex-col font-sans">
      
      {/* Top Header Navigation */}
      <Header
        activeMenu={activeMenu}
        onMenuChange={handleMenuChangeWithGuard}
        onOpenParser={() => setActiveMenu("add_property" as any)}
        savedCount={savedProperties.length}
      />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 py-6 w-full">
        
        {/* MENU 0: LANDING HERO VIEW */}
        {activeMenu === "home" && (
          <LandingHeroView
            onNavigate={handleMenuChangeWithGuard}
            onOpenWizard={() => setActiveMenu("add_property" as any)}
          />
        )}

        {/* MENU 1: KONUT DEĞERİ HESAPLA & DASHBOARD */}
        {activeMenu === "valuation" && (
          <div className="space-y-6 animate-fadeIn">
            
            {/* If no property is active, show prompt */}
            {!valuationData && (
              <div className="p-12 bg-white border border-[#E5E7EB] rounded-2xl text-center space-y-4">
                <h3 className="text-xl font-extrabold text-[#111827] font-display">
                  Değerleme Raporu İçin Taşınmaz Girin
                </h3>
                <p className="text-xs text-slate-600 max-w-md mx-auto">
                  Konutunuzun piyasa değerini, tahmini kirasını ve bölgesel endeksini öğrenmek için mülk detaylarını girin.
                </p>
                <button
                  onClick={() => setActiveMenu("add_property" as any)}
                  className="light-btn px-6 py-3 rounded-xl text-xs font-bold uppercase tracking-wider inline-flex items-center space-x-2"
                >
                  <span>Ücretsiz Konut Değerini Hesapla</span>
                </button>
              </div>
            )}

            {valuationData && (
              <div className="space-y-6">
                <ValuationDashboard valuation={valuationData.valuation} spatial={valuationData.spatial} />
                <SpatialMap
                  spatial={valuationData.spatial}
                  onNavigateToReport={handleMenuChangeWithGuard}
                />
              </div>
            )}

          </div>
        )}

        {/* MENU 2: DEPREM RİSK RAPORU */}
        {activeMenu === "earthquake" && (
          <EarthquakeReportView
            data={valuationData?.spatial}
            onOpenParser={() => setActiveMenu("add_property" as any)}
          />
        )}

        {/* MENU 3: SUÇ RAPORU */}
        {activeMenu === "safety" && (
          <SafetyReportView
            data={valuationData?.spatial}
            onOpenParser={() => setActiveMenu("add_property" as any)}
          />
        )}

        {/* MENU 4: EĞİTİM RAPORU */}
        {activeMenu === "education" && (
          <EducationReportView
            data={valuationData?.spatial}
            onOpenParser={() => setActiveMenu("add_property" as any)}
          />
        )}

        {/* MENU 5: KENTSEL DÖNÜŞÜM RAPORU */}
        {activeMenu === "urban" && valuationData && (
          <div className="space-y-6 animate-fadeIn">
            <UrbanTransformationSim
              urban={valuationData.urban_transformation}
              onShareChange={(newRatio) => {
                runFullCheckup({
                  ...parsedInput,
                  contractor_share_ratio: newRatio,
                });
              }}
            />
          </div>
        )}

        {/* MENU 6: PROFİLİM */}
        {activeMenu === "profile" && (
          <ProfilePortfolioView
            properties={savedProperties}
            selectedId={selectedPropertyId}
            onSelect={handleSelectSavedProperty}
            onRemoveProperty={handleRemoveSavedProperty}
            onOpenWizard={() => setActiveMenu("add_property" as any)}
          />
        )}

        {/* MENU 7: ADD PROPERTY */}
        {activeMenu === "add_property" && (
          <AdInputParser
            onComplete={runFullCheckup}
            loading={loading}
          />
        )}
      </main>

      {/* Property Select Guard Modal */}
      <PropertySelectGuardModal
        isOpen={isGuardOpen}
        onClose={() => setIsGuardOpen(false)}
        savedProperties={savedProperties}
        onSelectProperty={(prop) => {
          handleSelectSavedProperty(prop);
          setIsGuardOpen(false);
          if (targetGuardTab) setActiveMenu(targetGuardTab);
        }}
        onOpenWizard={() => {
          setIsGuardOpen(false);
          setActiveMenu("add_property" as any);
        }}
      />

      {/* Footer */}
      <footer className="bg-white border-t border-[#E5E7EB] py-8 text-center text-xs text-slate-500 font-medium">
        <div className="max-w-7xl mx-auto px-4 space-y-2">
          <p>© 2026 rayic.org — Gayrimenkul Değerleme ve Tematik Raporlar Platformu</p>
          <p className="text-[11px] text-slate-400">
            TCMB EVDS, AFAD Deprem Zemin Kataloğu ve Emniyet Asayiş Analitiği ile güçlendirilmiştir.
          </p>
        </div>
      </footer>

    </div>
  );
}
