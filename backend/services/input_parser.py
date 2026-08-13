import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ParsedAdInput(BaseModel):
    raw_text: str
    price: Optional[float] = None
    currency: str = "TRY"
    net_m2: Optional[float] = None
    gross_m2: Optional[float] = None
    building_age: Optional[int] = None
    floor: Optional[str] = None
    floor_category: str = "ara_kat"  # bodrum, giris, ara_kat, en_ust
    room_count: Optional[str] = None
    land_share_num: Optional[float] = None
    land_share_den: Optional[float] = None
    district: Optional[str] = None
    neighborhood: Optional[str] = None
    missing_fields: List[str] = []

KNOWN_DISTRICTS = {
    "kadıköy": ["caferağa", "caddebostan", "suadiye", "fenerbahçe", "göztepe", "bostancı", "moda"],
    "maltepe": ["yalı", "küçükyalı", "altıntepe", "idealtepe", "cevizli"],
    "beşiktaş": ["bebek", "etiler", "levent", "akatlar", "arnavutköy", "dikilitaş"],
    "şişli": ["nişantaşı", "teşvikiye", "mecidiyeköy", "fulya", "bomonti"],
    "üsküdar": ["kuzguncuk", "çengelköy", "kandilli", "beylerbeyi", "altunizade"]
}

def parse_ad_text(text: str) -> ParsedAdInput:
    cleaned = text.strip()
    
    # 1. Price Parsing
    price = None
    # Patterns: 12.500.000 TL, 12,5M, 4.5 Milyon, 12500000 ₺, 750k TL
    price_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*(milyon|m|k|bin)?\s*(?:tl|₺|try)?', cleaned, re.IGNORECASE)
    
    # Direct currency number search like 12.500.000 TL or 12.500.000₺ or Fiyat: 15.000.000
    price_full_match = re.search(r'(?:fiyat|ücret|bedel)?\s*:?\s*(\d{1,3}(?:\.\d{3})+|\d{5,10})\s*(?:tl|₺|try)?', cleaned, re.IGNORECASE)
    
    if price_full_match:
        val_str = price_full_match.group(1).replace(".", "").replace(",", ".")
        try:
            price = float(val_str)
        except ValueError:
            pass
    elif price_match:
        val_str = price_match.group(1).replace(",", ".")
        multiplier_str = (price_match.group(2) or "").lower()
        try:
            base_val = float(val_str)
            if multiplier_str in ["milyon", "m"]:
                price = base_val * 1_000_000
            elif multiplier_str in ["k", "bin"]:
                price = base_val * 1_000
            elif base_val > 100_000:
                price = base_val
        except ValueError:
            pass

    # 2. Net / Gross m2
    net_m2 = None
    gross_m2 = None
    
    net_match = re.search(r'net\s*(?:m2|m²|metrekare)?\s*:?\s*(\d+(?:[\.,]\d+)?)', cleaned, re.IGNORECASE)
    if not net_match:
        net_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:m2|m²|metrekare)\s*net', cleaned, re.IGNORECASE)
    if net_match:
        try:
            net_m2 = float(net_match.group(1).replace(",", "."))
        except ValueError:
            pass
            
    gross_match = re.search(r'brüt\s*(?:m2|m²|metrekare)?\s*:?\s*(\d+(?:[\.,]\d+)?)', cleaned, re.IGNORECASE)
    if not gross_match:
        gross_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:m2|m²|metrekare)\s*brüt', cleaned, re.IGNORECASE)
    if gross_match:
        try:
            gross_m2 = float(gross_match.group(1).replace(",", "."))
        except ValueError:
            pass
            
    # Generic m2 fallback
    if not net_m2 and not gross_m2:
        m2_match = re.search(r'(\d{2,4})\s*(?:m2|m²|metrekare)', cleaned, re.IGNORECASE)
        if m2_match:
            val = float(m2_match.group(1))
            net_m2 = val * 0.85  # Estimate net as 85% of total m2
            gross_m2 = val

    # 3. Building Age
    building_age = None
    age_match = re.search(r'(?:bina\s*yaşı|yaş|yaşında)?\s*:?\s*(\d{1,2})\s*(?:yaş|yaşında|yıllık)', cleaned, re.IGNORECASE)
    if age_match:
        try:
            building_age = int(age_match.group(1))
        except ValueError:
            pass
    elif re.search(r'\b(sıfır|0\s*yaş|yeni\s*bina)\b', cleaned, re.IGNORECASE):
        building_age = 0

    # 4. Floor Info & Category
    floor = None
    floor_cat = "ara_kat"
    
    floor_match = re.search(r'(\d+)\.\s*kat|kat\s*:?\s*(\d+|giriş|bodrum|bahçe|çatı|en üst)', cleaned, re.IGNORECASE)
    if floor_match:
        floor = floor_match.group(0)
        floor_str = floor.lower()
        if "bodrum" in floor_str:
            floor_cat = "bodrum"
        elif "giriş" in floor_str or "bahçe" in floor_str or "zemin" in floor_str:
            floor_cat = "giris"
        elif "çatı" in floor_str or "en üst" in floor_str:
            floor_cat = "en_ust"
        else:
            floor_cat = "ara_kat"
    elif "bodrum" in cleaned.lower():
        floor_cat = "bodrum"
        floor = "Bodrum Kat"
    elif "giriş" in cleaned.lower() or "zemin" in cleaned.lower():
        floor_cat = "giris"
        floor = "Giriş Kat"

    # 5. Room Count
    room_count = None
    room_match = re.search(r'(\d\+\d)', cleaned)
    if room_match:
        room_count = room_match.group(1)

    # 6. Land Share (Arsa Payı)
    land_num = None
    land_den = None
    land_match = re.search(r'arsa\s*payı\s*:?\s*(\d+)\s*[/:\\]\s*(\d+)', cleaned, re.IGNORECASE)
    if not land_match:
        land_match = re.search(r'(\d+)\s*[/:\\]\s*(\d+)\s*arsa\s*payı', cleaned, re.IGNORECASE)
    if land_match:
        try:
            land_num = float(land_match.group(1))
            land_den = float(land_match.group(2))
        except ValueError:
            pass

    # 7. District & Neighborhood Detection
    district = None
    neighborhood = None
    cleaned_lower = cleaned.lower()
    for d, n_list in KNOWN_DISTRICTS.items():
        if d in cleaned_lower:
            district = d.capitalize()
            for n in n_list:
                if n in cleaned_lower:
                    neighborhood = n.capitalize()
                    break
            break
            
    if not district:
        # Default fallback to Kadıköy / Caddebostan if unspecified
        district = "Kadıköy"
        neighborhood = "Caddebostan"

    # Identify Missing Fields for UX Interceptor
    missing = []
    if price is None or price <= 0:
        missing.append("price")
    if net_m2 is None or net_m2 <= 0:
        missing.append("net_m2")
    if building_age is None:
        missing.append("building_age")
    if land_num is None or land_den is None:
        missing.append("land_share")

    return ParsedAdInput(
        raw_text=text,
        price=price,
        net_m2=net_m2,
        gross_m2=gross_m2 or (net_m2 * 1.18 if net_m2 else None),
        building_age=building_age,
        floor=floor or "3. Kat",
        floor_category=floor_cat,
        room_count=room_count or "3+1",
        land_share_num=land_num,
        land_share_den=land_den,
        district=district,
        neighborhood=neighborhood,
        missing_fields=missing
    )
