from typing import Dict, Any, Optional
from pydantic import BaseModel

from services.valuation_engine import piyasa_kiralik, segment_duzeltme, PIYASA_META
from services.location_factor import konum_carpani

class FinancialYieldResult(BaseModel):
    estimated_monthly_rent: float
    annual_gross_rent: float
    kira_rayic_tlm2: Optional[float] = None
    kira_rayic_kaynak: str = "-"
    kira_konum_carpani: Optional[float] = None
    kira_yas_carpani: Optional[float] = None
    kira_segment_carpani: Optional[float] = None
    gross_yield_percent: float
    net_yield_percent: float
    amortization_years: float
    amortization_months: int
    investment_rating: str
    benchmark_comparison: Dict[str, float]

# YEDEK: yalnızca güncel rayiç bulunamazsa kullanılır. Eskiden ANA kaynak
# buydu (5 ilçe, gerisi 380 TL/m²) — oysa elimizde 39 ilçe / 479 mahallelik
# Ağustos 2026 kira rayici var (ör. Caddebostan 939 TL/m², bu tablo 420 diyordu).
DISTRICT_RENTAL_RATES = {
    "Kadıköy": 420.0,
    "Maltepe": 280.0,
    "Beşiktaş": 550.0,
    "Şişli": 450.0,
    "Üsküdar": 350.0
}


def calculate_financials(
    advertised_price: float,
    net_m2: float,
    district: str = "Kadıköy",
    building_age: int = 10,
    neighborhood: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    site_icinde: Optional[bool] = None,
) -> FinancialYieldResult:
    """Kira, satış değerlemesiyle AYNI değişkenlere dayanır:

      güncel mahalle kira rayici x yaş x mahalle-içi konum x büyüklük segmenti

    Konum çarpanı satış tarafındakiyle aynı ölçülmüş katsayılardan gelir
    (kıyı/raylı sistem yakınlığı); kira da konuma göre değişir, tek bir ilçe
    ortalaması kullanmak gerçekçi değildi."""
    # 1) Güncel mahalle kira rayici (Ağustos 2026); yoksa ilçe medyanı; o da
    #    yoksa eski sabit tablo.
    rate_per_m2 = piyasa_kiralik(district, neighborhood)
    if rate_per_m2:
        kaynak = str(PIYASA_META.get("source", "Ağustos 2026 piyasa raporu"))
    else:
        rate_per_m2 = DISTRICT_RENTAL_RATES.get(district, 380.0)
        kaynak = "yedek sabit tablo (güncel rayiç bulunamadı)"

    # 2) Bina yaşı
    if building_age <= 3:
        rent_age_factor = 1.20
    elif building_age <= 10:
        rent_age_factor = 1.05
    elif building_age <= 20:
        rent_age_factor = 0.95
    else:
        rent_age_factor = 0.80

    # 3) Mahalle İÇİ konum (kıyıya/raylı sisteme yakınlık) — satışla aynı model
    _loc = konum_carpani(lat, lng, district, neighborhood)
    k_loc = float(_loc["carpan"]) if _loc else 1.0

    # 4) Büyüklük segmenti: küçük daireler m² başına daha yüksek kiralanır
    k_seg, _ = segment_duzeltme(net_m2, site_icinde)

    estimated_monthly_rent = net_m2 * rate_per_m2 * rent_age_factor * k_loc * k_seg
    annual_gross_rent = estimated_monthly_rent * 12.0
    
    gross_yield = (annual_gross_rent / advertised_price) * 100.0 if advertised_price > 0 else 0.0
    net_annual_rent = annual_gross_rent * 0.85  # Deducing 15% taxes, maintenance, vacancy
    net_yield = (net_annual_rent / advertised_price) * 100.0 if advertised_price > 0 else 0.0
    
    amortization_years = (advertised_price / annual_gross_rent) if annual_gross_rent > 0 else 0.0
    amortization_months = int(round(amortization_years * 12))
    
    if amortization_years < 16.0:
        rating = "Mükemmel Getiri - Hızlı Amortisman"
    elif amortization_years <= 20.0:
        rating = "Makul Piyasa Ortalaması"
    else:
        rating = "Düşük Kira Getirisi - Prim Odaklı Mülk"

    return FinancialYieldResult(
        estimated_monthly_rent=round(estimated_monthly_rent, 0),
        annual_gross_rent=round(annual_gross_rent, 0),
        kira_rayic_tlm2=round(float(rate_per_m2), 2),
        kira_rayic_kaynak=kaynak,
        kira_konum_carpani=round(k_loc, 3),
        kira_yas_carpani=rent_age_factor,
        kira_segment_carpani=k_seg,
        gross_yield_percent=round(gross_yield, 2),
        net_yield_percent=round(net_yield, 2),
        amortization_years=round(amortization_years, 1),
        amortization_months=amortization_months,
        investment_rating=rating,
        benchmark_comparison={
            "istanbul_average_years": 19.5,
            "district_average_years": round(amortization_years * 0.95, 1),
            "deposit_interest_equivalent_yield": 42.0
        }
    )
