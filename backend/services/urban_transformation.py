from typing import Dict, Any, Optional
from pydantic import BaseModel

class UrbanTransformationResult(BaseModel):
    current_net_m2: float
    land_share_m2: float
    contractor_share_percent: float
    new_flat_net_m2: float
    estimated_new_building_price: float
    value_appreciation_percent: float
    roi_status_label: str
    breakdown_notes: Dict[str, str]

# Neighborhood Contractor Share Ratios Map (User Customizable)
NEIGHBORHOOD_CONTRACTOR_RATIOS: Dict[str, float] = {
    "Caddebostan": 0.42,
    "Suadiye": 0.45,
    "Fenerbahçe": 0.40,
    "Caferağa (Moda)": 0.45,
    "Göztepe": 0.50,
    "Bostancı": 0.50,
    "Küçükyalı": 0.52,
    "Bebek": 0.38,
    "Nişantaşı": 0.40,
    "Kuzguncuk": 0.42,
    "Florya": 0.45,
    "default": 0.50
}

def simulate_urban_transformation(
    advertised_price: float,
    current_net_m2: float,
    total_land_m2: Optional[float] = 2400.0,
    land_num: Optional[float] = 15.0,
    land_den: Optional[float] = 240.0,
    contractor_share_ratio: Optional[float] = None,
    district: str = "Kadıköy",
    neighborhood: str = "Caddebostan"
) -> UrbanTransformationResult:
    
    # Calculate Land Share m2
    num = land_num if (land_num and land_num > 0) else 15.0
    den = land_den if (land_den and land_den > 0) else 240.0
    total_land = total_land_m2 if (total_land_m2 and total_land_m2 > 0) else 2400.0
    
    land_share_m2 = (num / den) * total_land

    # Determine contractor ratio from neighborhood map or custom user input
    if contractor_share_ratio is not None and 0.1 <= contractor_share_ratio <= 0.8:
        final_ratio = contractor_share_ratio
    else:
        final_ratio = NEIGHBORHOOD_CONTRACTOR_RATIOS.get(
            neighborhood, NEIGHBORHOOD_CONTRACTOR_RATIOS.get("default", 0.50)
        )

    # New Flat m2 estimation after urban renewal
    new_flat_net_m2 = land_share_m2 * (1.0 - final_ratio) * 1.15
    if new_flat_net_m2 < 45.0:
        new_flat_net_m2 = 45.0

    # New Building Price Estimation (+60% value appreciation for new A-class building)
    estimated_new_building_price = advertised_price * 1.65
    value_appreciation_percent = 65.0

    return UrbanTransformationResult(
        current_net_m2=current_net_m2,
        land_share_m2=round(land_share_m2, 2),
        contractor_share_percent=round(final_ratio * 100.0, 1),
        new_flat_net_m2=round(new_flat_net_m2, 1),
        estimated_new_building_price=round(estimated_new_building_price, 2),
        value_appreciation_percent=value_appreciation_percent,
        roi_status_label="YÜKSEK PRİM VE DÖNÜŞÜM POTANSİYELİ",
        breakdown_notes={
            "land_share": f"Arsa Payı: {num}/{den} ({round(land_share_m2, 1)} m² net arsa hakkı)",
            "contractor_ratio": f"Bölge Müteahhit Payı: %{round(final_ratio * 100.0, 1)}",
            "new_flat": f"Yeni Sıfır Daire Net Alanı: ~{round(new_flat_net_m2, 1)} m²",
            "appreciation": f"Dönüşüm Sonrası Tahmini Değer: {round(estimated_new_building_price, 0):,.0f} ₺ (+%65 Prim)"
        }
    )
