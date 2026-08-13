from typing import Dict, Any, Optional
from pydantic import BaseModel
from services.tcmb_service import get_tcmb_kfe_summary

class ValuationResult(BaseModel):
    base_m2_price: float
    estimated_total_price: float
    advertised_price: float
    price_per_m2_advertised: float
    deviation_percent: float
    deal_status: str
    status_label: str
    status_color: str
    k_age: float
    k_floor: float
    k_facade: float
    k_tcmb: float
    tcmb_macro_impact_tl: float
    valuation_breakdown: Dict[str, float]

# Comprehensive baseline matrix for ALL 39 Istanbul Districts (TL / Net m2)
DISTRICT_BASE_PRICES: Dict[str, Dict[str, float]] = {
    "Kadıköy": {"Caddebostan": 115000.0, "Suadiye": 110000.0, "Fenerbahçe": 125000.0, "Caferağa (Moda)": 105000.0, "Göztepe": 90000.0, "Bostancı": 85000.0, "default": 100000.0},
    "Maltepe": {"Küçükyalı": 60000.0, "Yalı Mahallesi": 65000.0, "Altıntepe": 58000.0, "İidealtepe": 62000.0, "default": 55000.0},
    "Beşiktaş": {"Bebek": 210000.0, "Etiler": 175000.0, "Levent": 160000.0, "Arnavutköy": 190000.0, "Ulus": 180000.0, "default": 150000.0},
    "Şişli": {"Nişantaşı": 165000.0, "Teşvikiye": 155000.0, "Bomonti": 110000.0, "Mecidiyeköy": 85000.0, "default": 105000.0},
    "Üsküdar": {"Kuzguncuk": 140000.0, "Çengelköy": 115000.0, "Kandilli": 130000.0, "Beylerbeyi": 125000.0, "default": 90000.0},
    "Ataşehir": {"Batı Ataşehir": 110000.0, "Atatürk": 95000.0, "Barbaros": 90000.0, "default": 75000.0},
    "Bakırköy": {"Florya": 150000.0, "Yeşilköy": 135000.0, "Ataköy": 120000.0, "default": 110000.0},
    "Sarıyer": {"İstinye": 180000.0, "Yeniköy": 195000.0, "Maslak": 140000.0, "Zekeriyaköy": 125000.0, "default": 150000.0},
    "Ümraniye": {"Elmalıkent": 50000.0, "Yamanevler": 52000.0, "Şerifali": 60000.0, "default": 52000.0},
    "Beylikdüzü": {"Adnan Kahveci": 42000.0, "Barış": 40000.0, "Yakuplu": 35000.0, "default": 38000.0},
    "Kartal": {"Kordonboyu": 65000.0, "Yalı": 58000.0, "Atalar": 52000.0, "default": 52000.0},
    "Pendik": {"Batı": 58000.0, "Yenişehir": 55000.0, "Kurtköy": 48000.0, "default": 50000.0},
    "Fatih": {"Sultanahmet": 95000.0, "Balat": 75000.0, "Aksaray": 65000.0, "default": 65000.0},
    "Beyoğlu": {"Cihangir": 145000.0, "Galata": 135000.0, "Karaköy": 125000.0, "default": 110000.0},
    "Zeytinburnu": {"Kazlıçeşme": 95000.0, "Merkezefendi": 65000.0, "default": 60000.0},
    "Kağıthane": {"Seyrantepe": 75000.0, "Hamidiye": 68000.0, "default": 62000.0},
    "Eyüpsultan": {"Göktürk": 125000.0, "Kemerburgaz": 115000.0, "Alibeyköy": 48000.0, "default": 75000.0},
    "Bahçelievler": {"Basın Sitesi": 52000.0, "Yenibosna": 45000.0, "default": 48000.0},
    "Bağcılar": {"Güneşli": 45000.0, "Mahmutbey": 42000.0, "default": 40000.0},
    "Esenler": {"Birlik": 38000.0, "default": 38000.0},
    "Güngören": {"Merter": 65000.0, "Haznedar": 48000.0, "default": 48000.0},
    "Avcılar": {"Denizköşkler": 42000.0, "Ambarlı": 38000.0, "default": 38000.0},
    "Küçükçekmece": {"Halkalı": 58000.0, "Atakent": 65000.0, "Cennet": 52000.0, "default": 50000.0},
    "Büyükçekmece": {"Mimaroba": 45000.0, "Kumburgaz": 38000.0, "default": 40000.0},
    "Başakşehir": {"Bahçeşehir 1. Kısım": 75000.0, "Kayabaşı": 48000.0, "default": 55000.0},
    "Esenyurt": {"Güzelyurt": 32000.0, "Cumhuriyet": 35000.0, "default": 30000.0},
    "Tuzla": {"Postane": 58000.0, "Aydınlı": 42000.0, "default": 48000.0},
    "Sancaktepe": {"Samandıra": 42000.0, "default": 40000.0},
    "Sultanbeyli": {"Abdurrahmangazi": 35000.0, "default": 35000.0},
    "Çekmeköy": {"Mimar Sinan": 55000.0, "Alemdağ": 48000.0, "default": 50000.0},
    "Beykoz": {"Kavacık": 95000.0, "Kanlıca": 140000.0, "Riva": 85000.0, "default": 90000.0},
    "Gaziosmanpaşa": {"Merkez": 45000.0, "default": 42000.0},
    "Sultangazi": {"Gazi": 38000.0, "default": 38000.0},
    "Arnavutköy": {"Hadımköy": 38000.0, "default": 35000.0},
    "Silivri": {"Selimpaşa": 38000.0, "default": 35000.0},
    "Çatalca": {"Kaleici": 35000.0, "default": 32000.0},
    "Şile": {"Çavuş": 52000.0, "Ağva": 45000.0, "default": 48000.0},
    "Adalar": ["Büyükada", "Heybeliada"],
    "Adalar": {"Büyükada": 110000.0, "Heybeliada": 95000.0, "default": 95000.0},
    "Bayrampaşa": {"Kartaltepe": 48000.0, "default": 45000.0}
}

def get_base_m2_price(district: Optional[str], neighborhood: Optional[str]) -> float:
    dist = district or "Kadıköy"
    neigh = neighborhood or "Caddebostan"
    
    dist_dict = DISTRICT_BASE_PRICES.get(dist, DISTRICT_BASE_PRICES["Kadıköy"])
    if isinstance(dist_dict, dict):
        return dist_dict.get(neigh, dist_dict.get("default", 60000.0))
    return 60000.0

def get_age_coefficient(age: Optional[int]) -> float:
    if age is None:
        return 1.0
    if age <= 3:
        return 1.15
    elif age <= 10:
        return 1.05
    elif age <= 20:
        return 0.95
    else:
        return 0.80

def get_floor_coefficient(floor_cat: str) -> float:
    cat = (floor_cat or "ara_kat").lower()
    if cat == "bodrum":
        return 0.85
    elif cat in ["giris", "zemin", "bahce"]:
        return 0.90
    elif cat in ["en_ust", "cati"]:
        return 1.00
    else:
        return 1.10

def calculate_valuation(
    price_advertised: float,
    net_m2: float,
    building_age: Optional[int] = None,
    floor_category: str = "ara_kat",
    district: Optional[str] = "Kadıköy",
    neighborhood: Optional[str] = "Caddebostan",
    k_facade: float = 1.0
) -> ValuationResult:
    base_m2 = get_base_m2_price(district, neighborhood)
    k_age = get_age_coefficient(building_age)
    k_floor = get_floor_coefficient(floor_category)
    
    tcmb_data = get_tcmb_kfe_summary()
    latest_kfe = tcmb_data.get("latest_istanbul_index", 1880.0)
    base_kfe = 1455.5
    
    k_tcmb = round(latest_kfe / base_kfe, 3)
    raw_estimated_price = base_m2 * net_m2 * k_age * k_floor * k_facade * k_tcmb
    tcmb_impact_tl = raw_estimated_price - (base_m2 * net_m2 * k_age * k_floor * k_facade)
    
    deviation = ((price_advertised - raw_estimated_price) / raw_estimated_price) * 100.0
    
    if deviation < -10.0:
        deal_status = "firsat"
        status_label = "FIRSAT İLAN (PİYASA ALTINDA)"
        status_color = "#047857"
    elif -10.0 <= deviation <= 10.0:
        deal_status = "makul"
        status_label = "MAKUL PİYASA DEĞERİ"
        status_color = "#111827"
    else:
        deal_status = "asiri_fiyatli"
        status_label = "AŞIRI FİYATLANMIŞ / RİSKLİ"
        status_color = "#C2410C"
        
    price_per_m2_adv = price_advertised / net_m2 if net_m2 > 0 else 0.0

    return ValuationResult(
        base_m2_price=base_m2,
        estimated_total_price=round(raw_estimated_price, 2),
        advertised_price=price_advertised,
        price_per_m2_advertised=round(price_per_m2_adv, 2),
        deviation_percent=round(deviation, 2),
        deal_status=deal_status,
        status_label=status_label,
        status_color=status_color,
        k_age=k_age,
        k_floor=k_floor,
        k_facade=k_facade,
        k_tcmb=k_tcmb,
        tcmb_macro_impact_tl=round(tcmb_impact_tl, 2),
        valuation_breakdown={
            "base_m2": base_m2,
            "net_m2": net_m2,
            "k_age": k_age,
            "k_floor": k_floor,
            "k_facade": k_facade,
            "k_tcmb": k_tcmb,
            "tcmb_impact_tl": tcmb_impact_tl,
            "raw_valuation": raw_estimated_price
        }
    )
