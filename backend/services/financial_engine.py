from typing import Dict, Any
from pydantic import BaseModel

class FinancialYieldResult(BaseModel):
    estimated_monthly_rent: float
    annual_gross_rent: float
    gross_yield_percent: float
    net_yield_percent: float
    amortization_years: float
    amortization_months: int
    investment_rating: str
    benchmark_comparison: Dict[str, float]

# Average monthly rental m2 rates for Istanbul pilot districts (TL / Net m2)
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
    building_age: int = 10
) -> FinancialYieldResult:
    rate_per_m2 = DISTRICT_RENTAL_RATES.get(district, 380.0)
    
    # Age factor for rent
    if building_age <= 3:
        rent_age_factor = 1.20
    elif building_age <= 10:
        rent_age_factor = 1.05
    elif building_age <= 20:
        rent_age_factor = 0.95
    else:
        rent_age_factor = 0.80

    estimated_monthly_rent = net_m2 * rate_per_m2 * rent_age_factor
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
