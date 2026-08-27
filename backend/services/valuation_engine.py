import os
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel
from services.tcmb_service import get_tcmb_kfe_summary, get_inflation_factor

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
    base_price_source: str = "-"
    base_price_sample_n: int = 0
    data_collection_date: str = "-"
    inflation_factor: float = 1.0
    base_m2_price_historical: float = 0.0
    yas_bandi: str = "-"
    sifir_konut_prim_pct: Optional[float] = None
    kiralik_rayic_tlm2: Optional[float] = None
    trend_yillik_nominal_pct: Optional[float] = None
    projeksiyon_12ay_tlm2: Optional[float] = None
    projeksiyon_24ay_tlm2: Optional[float] = None
    # Mahalle içi fiyat saçılması: nokta tahmin yerine aralık ver.
    deger_alt_tl: Optional[float] = None
    deger_ust_tl: Optional[float] = None
    mahalle_iqr_orani: Optional[float] = None
    mahalle_heterojen: bool = False
    mahalle_ilan_n: Optional[int] = None
    segment_duzeltme: Optional[float] = None
    segment_etiketi: Optional[str] = None
    valuation_breakdown: Dict[str, float]


# ---------------------------------------------------------------------------
# Real market base prices: median second-hand TL/m² per district & mahalle,
# aggregated from ~14k scraped EmlakJet İstanbul listings (methodology adapted
# from the EmlakJet house-price-prediction projects). Loaded from
# data/emlakjet_m2_prices.json.
# ---------------------------------------------------------------------------
def _load_emlakjet_prices() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "emlakjet_m2_prices.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"meta": {}, "prices": {}}


_EMLAKJET = _load_emlakjet_prices()
EMLAKJET_PRICES: Dict[str, Any] = _EMLAKJET.get("prices", {})
EMLAKJET_META: Dict[str, Any] = _EMLAKJET.get("meta", {})


def _load_age_premium() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "age_premium.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_AGE_PREMIUM = _load_age_premium()
_AGE_GENEL: Dict[str, float] = _AGE_PREMIUM.get("istanbul_geneli_carpan", {})
_AGE_ILCE: Dict[str, Any] = _AGE_PREMIUM.get("ilceler", {})


def _load_piyasa() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "piyasa_rayic.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_PIYASA = _load_piyasa()
PIYASA_RAYIC: Dict[str, Any] = _PIYASA.get("rayic", {})
PIYASA_META: Dict[str, Any] = _PIYASA.get("meta", {})


# ---------------------------------------------------------------------------
# Mahalle İÇİ fiyat saçılması. İstanbul'da mahalleler geniş ve heterojen:
# ölçtüğümüz kadarıyla tipik mahallede çeyrekler arası açıklık medyanın %40'ı,
# en uçta %200'ü buluyor. Bu yüzden tek bir m² fiyatıyla nokta tahmin yapmak
# ekspertizi yanıltıcı kılıyor -> ARALIK + heterojenlik uyarısı veriyoruz.
# Ayrıca mahalle medyanının SİSTEMATİK saptığı segmentleri düzeltiyoruz
# (küçük daire / çok büyük daire / site içi) — çapraz doğrulamayla sınandı.
# ---------------------------------------------------------------------------
def _load_dispersion() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "mahalle_dispersion.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_DISP = _load_dispersion()
DISP_META: Dict[str, Any] = _DISP.get("meta", {})


def _disp_lookup(district: Optional[str], neighborhood: Optional[str]) -> Optional[Dict[str, Any]]:
    for ilce, mahs in (_DISP.get("mahalle") or {}).items():
        if _norm_tr(ilce) != _norm_tr(district or ""):
            continue
        for m, rec in mahs.items():
            if _norm_tr(m) == _norm_tr(neighborhood or ""):
                return rec
    return None


def segment_duzeltme(net_m2: Optional[float], site_icinde: Optional[bool] = None):
    """Mahalle medyanının sistematik saptığı segmentler için çarpan.

    Ölçüm (örneklem dışı, 5-katlı): mahalle medyanı küçük daireleri ~%9,
    çok büyük daireleri ~%19, site içi konutları ~%12 DÜŞÜK gösteriyor.
    Bu çarpanlar o yanlılığı sıfıra yaklaştırıyor. Döner: (çarpan, etiket)."""
    if not net_m2 or net_m2 <= 0:
        return 1.0, None
    bins = _DISP.get("segment_sinirlari") or [0, 60, 90, 140, 250, 600]
    labels = list((_DISP.get("segment_carpani") or {}).keys())
    if not labels:
        return 1.0, None
    order = ["<60", "60-90", "90-140", "140-250", "250+"]
    label = order[-1]
    for i in range(1, len(bins)):
        if net_m2 <= bins[i]:
            label = order[min(i - 1, len(order) - 1)]
            break
    mult = float((_DISP.get("segment_carpani") or {}).get(label, 1.0))
    if site_icinde:
        mult *= float((_DISP.get("site_carpani") or {}).get("1", 1.0))
    return round(mult, 3), label


def _age_multiplier(district: Optional[str], band: str) -> float:
    for k, v in _AGE_ILCE.items():
        if _norm_tr(k) == _norm_tr(district or ""):
            c = v.get("carpanlar", {})
            if band in c:
                return c[band]
    return _AGE_GENEL.get(band, 1.0)


def _load_market_trend() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "market_trend.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_MARKET_TREND = _load_market_trend()
_TREND_ILCE: Dict[str, float] = _MARKET_TREND.get("ilce_yillik_nominal_pct", {})
_TREND_ISTANBUL: float = float(_MARKET_TREND.get("istanbul_yillik_nominal_pct", 17.5))


def market_projection(district: Optional[str], current_tlm2: float) -> Dict[str, Any]:
    """Fiyat trendi + market projeksiyonu. Trend, EmlakJet(2024-09)→piyasa
    raporu(2026-06) gerçekleşen yıllık nominal büyümeden; TCMB KFE makro endeks
    YoY bağlam olarak eklenir. Projeksiyon = güncel × (1+trend)^yıl."""
    # İlçe gerçekleşen trendi (kaynak gürültüsü içerir) ile İstanbul genelini
    # 50/50 blend'le — daha kararlı bir yerel trend.
    ilce_yr = None
    for k, v in _TREND_ILCE.items():
        if _norm_tr(k) == _norm_tr(district or ""):
            ilce_yr = float(v)
            break
    if ilce_yr is not None:
        yr = 0.5 * ilce_yr + 0.5 * _TREND_ISTANBUL
    else:
        yr = _TREND_ISTANBUL
    yr = max(6.0, min(35.0, yr))
    r = yr / 100.0
    kfe_yoy = get_tcmb_kfe_summary().get("nominal_change_yoy")
    return {
        "trend_yillik_nominal_pct": round(yr, 1),
        "kfe_makro_yoy_pct": kfe_yoy,
        "projeksiyon_12ay_tlm2": round(current_tlm2 * (1 + r)),
        "projeksiyon_24ay_tlm2": round(current_tlm2 * (1 + r) ** 2),
    }


def piyasa_kiralik(district: Optional[str], neighborhood: Optional[str]) -> Optional[float]:
    """Ağustos 2026 raporundan güncel mahalle kira rayici (TL/m²)."""
    if not district:
        return None
    for k, v in PIYASA_RAYIC.items():
        if _norm_tr(k) == _norm_tr(district):
            for mk, mv in v.items():
                if _norm_tr(mk) == _norm_tr(neighborhood or ""):
                    return mv.get("kiralik")
    return None


def age_premium_info(district: Optional[str], building_age: Optional[int]) -> Dict[str, Any]:
    """Sıfır (0-4 yaş) konutun, bu binanın yaş bandına göre m² prim farkı.
    EmlakJet yaş-bantlı verisinden; ilçe verisi yoksa İstanbul geneli çarpan."""
    band = _age_band(building_age)
    mult = None
    ilce = None
    for k, v in _AGE_ILCE.items():
        if _norm_tr(k) == _norm_tr(district or ""):
            ilce = v
            break
    carp = (ilce or {}).get("carpanlar") if ilce else None
    if carp and band in carp and "0-4" in carp:
        this_m = carp[band]
        new_m = carp["0-4"]
    else:
        this_m = _AGE_GENEL.get(band)
        new_m = _AGE_GENEL.get("0-4")
    prim = None
    if this_m and new_m:
        prim = round((new_m / this_m - 1) * 100, 1)
    labels = {"0-4": "0-4 yaş (Sıfır/Yeni)", "5-10": "5-10 yaş", "11-20": "11-20 yaş", "21+": "21+ yaş (Eski)"}
    return {"yas_bandi": labels.get(band, band), "sifir_konut_prim_pct": prim}


def _norm_tr(s: Optional[str]) -> str:
    s = (s or "").strip().lower()
    for a, b in (("ı", "i"), ("İ", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"),
                 ("ö", "o"), ("ç", "c"), ("â", "a")):
        s = s.replace(a, b)
    return s

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

_AGE_BAND_LABEL = {"0-4": "0-4 yaş", "5-10": "5-10 yaş", "11-20": "11-20 yaş", "21+": "21+ yaş"}


def _age_band(age: Optional[int]) -> str:
    a = 20 if age is None else age
    if a <= 4:
        return "0-4"
    if a <= 10:
        return "5-10"
    if a <= 20:
        return "11-20"
    return "21+"


def _pick_band(bands: Dict[str, Any], band: str):
    """From a {band: {tlm2,n}, 'all': {...}} dict pick the age band, else 'all'.
    Returns (tlm2, n, age_specific) or None."""
    if band in bands:
        return float(bands[band]["tlm2"]), int(bands[band]["n"]), True
    if "all" in bands:
        return float(bands["all"]["tlm2"]), int(bands["all"]["n"]), False
    return None


def _emlakjet_lookup(district: Optional[str], neighborhood: Optional[str], building_age: Optional[int]):
    """Age-aware lookup of the real EmlakJet median TL/m² (at data-collection date).
    Returns (tlm2, source_label, sample_n, age_specific) or None."""
    if not district:
        return None
    dn = _norm_tr(district)
    d_entry = None
    for k, v in EMLAKJET_PRICES.items():
        if _norm_tr(k) == dn:
            d_entry = v
            break
    if not d_entry:
        return None
    band = _age_band(building_age)
    band_lbl = _AGE_BAND_LABEL[band]

    if neighborhood:
        nn = _norm_tr(neighborhood)
        for mk, mv in d_entry.items():
            if mk != "default" and _norm_tr(mk) == nn and isinstance(mv, dict):
                picked = _pick_band(mv, band)
                if picked:
                    tlm2, n, age_spec = picked
                    tag = band_lbl if age_spec else "tüm yaşlar"
                    return tlm2, f"Bölge piyasa medyanı · {mk} · {tag} ({n} ilan)", n, age_spec
    dd = d_entry.get("default")
    if isinstance(dd, dict):
        picked = _pick_band(dd, band)
        if picked:
            tlm2, n, age_spec = picked
            tag = band_lbl if age_spec else "tüm yaşlar"
            return tlm2, f"Bölge piyasa medyanı · {district} · {tag} ({n} ilan)", n, age_spec
    return None


def _piyasa_lookup(district: Optional[str], neighborhood: Optional[str], building_age: Optional[int]):
    """Ağustos 2026 GÜNCEL piyasa raporundan blended satılık rayici; binanın yaş
    bandına EmlakJet çarpanıyla uyarlanır. (tlm2, source, n=1, age_specific=True)."""
    if not district:
        return None
    dn = _norm_tr(district)
    dd = None
    for k, v in PIYASA_RAYIC.items():
        if _norm_tr(k) == dn:
            dd = v
            break
    if not dd:
        return None
    blended = None
    tag = None
    if neighborhood:
        nn = _norm_tr(neighborhood)
        for mk, mv in dd.items():
            if _norm_tr(mk) == nn and mv.get("satilik"):
                blended = float(mv["satilik"])
                tag = mk
                break
    if blended is None:
        vals = [mv["satilik"] for mv in dd.values() if mv.get("satilik")]
        if not vals:
            return None
        vals.sort()
        blended = float(vals[len(vals) // 2])
        tag = "%s ilçe medyanı" % district
    band = _age_band(building_age)
    tlm2 = round(blended * _age_multiplier(district, band))
    return tlm2, "Ağustos 2026 piyasa raporu · %s · %s" % (tag, _AGE_BAND_LABEL[band]), 1, True


def get_base_m2_price(district: Optional[str], neighborhood: Optional[str], building_age: Optional[int] = None):
    """(base_tlm2, source_label, sample_n, age_specific). Önce GÜNCEL Ağustos 2026
    piyasa raporu (yaş bandına uyarlanmış), sonra yaş-bantlı EmlakJet medyanı,
    sonra statik matris."""
    piy = _piyasa_lookup(district, neighborhood, building_age)
    if piy:
        return piy
    hit = _emlakjet_lookup(district, neighborhood, building_age)
    if hit:
        return hit

    # Legacy static fallback (kept for districts/mahalles not in the dataset).
    dist = district or "Kadıköy"
    neigh = neighborhood or "Caddebostan"
    dist_dict = DISTRICT_BASE_PRICES.get(dist, DISTRICT_BASE_PRICES["Kadıköy"])
    if isinstance(dist_dict, dict):
        price = dist_dict.get(neigh, dist_dict.get("default", 60000.0))
        return float(price), "Statik referans matrisi (yedek)", 0, False
    return 60000.0, "Varsayılan (yedek)", 0, False

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
    k_facade: float = 1.0,
    site_icinde: Optional[bool] = None,
) -> ValuationResult:
    _yas_info = age_premium_info(district, building_age)
    base_m2_hist, base_source, base_n, age_specific = get_base_m2_price(district, neighborhood, building_age)
    # If the base already encodes the building's age band, don't re-apply k_age
    # (that would double-count age). Otherwise fall back to the age coefficient.
    k_age = 1.0 if age_specific else get_age_coefficient(building_age)
    k_floor = get_floor_coefficient(floor_category)

    # Ağustos 2026 piyasa raporu GÜNCEL veridir -> enflasyon uygulanmaz. EmlakJet
    # medyanları 2024-09 snapshot'ıdır -> TCMB KFE ile bugüne şişirilir (yüksek
    # konut enflasyonu). k_tcmb bu from-date→bugün faktörüdür.
    is_current = base_source.startswith("Ağustos 2026")
    if is_current:
        data_date = "2026-06"
        k_tcmb = 1.0
    elif base_n > 0:
        data_date = str(EMLAKJET_META.get("data_collection_date", "2024-09"))
        k_tcmb = float(get_inflation_factor(data_date).get("factor", 1.0))
    else:
        data_date = "-"
        k_tcmb = round(float(get_tcmb_kfe_summary().get("latest_istanbul_index", 1880.0)) / 1455.5, 3)

    # Base m² brought to today's level.
    base_m2 = round(base_m2_hist * k_tcmb, 0)
    _proj = market_projection(district, base_m2)

    # Segment yanlılık düzeltmesi (küçük/çok büyük daire, site içi).
    k_seg, seg_label = segment_duzeltme(net_m2, site_icinde)

    price_before_inflation = base_m2_hist * net_m2 * k_age * k_floor * k_facade * k_seg
    raw_estimated_price = base_m2 * net_m2 * k_age * k_floor * k_facade * k_seg
    tcmb_impact_tl = raw_estimated_price - price_before_inflation

    # Mahalle içi saçılmadan güven aralığı: mahalle medyanı ile p25/p75 oranını
    # tahmine taşıyoruz. Veri yoksa ölçülen İstanbul geneli IQR/medyan kullanılır.
    _d = _disp_lookup(district, neighborhood)
    if _d and _d.get("medyan"):
        lo_r = _d["p25"] / _d["medyan"]
        hi_r = _d["p75"] / _d["medyan"]
        iqr_oran, heter, mah_n = _d["iqr_orani"], bool(_d.get("heterojen")), _d["n"]
    else:
        iqr_oran = float(DISP_META.get("medyan_iqr_orani", 0.40))
        lo_r, hi_r = 1.0 - iqr_oran / 2.0, 1.0 + iqr_oran / 2.0
        heter, mah_n = False, None
    deger_alt = round(raw_estimated_price * lo_r, 2)
    deger_ust = round(raw_estimated_price * hi_r, 2)

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
        base_price_source=base_source,
        base_price_sample_n=base_n,
        data_collection_date=data_date,
        inflation_factor=round(k_tcmb, 3),
        base_m2_price_historical=round(base_m2_hist, 0),
        yas_bandi=_yas_info["yas_bandi"],
        sifir_konut_prim_pct=_yas_info["sifir_konut_prim_pct"],
        kiralik_rayic_tlm2=piyasa_kiralik(district, neighborhood),
        deger_alt_tl=deger_alt,
        deger_ust_tl=deger_ust,
        mahalle_iqr_orani=round(float(iqr_oran), 3),
        mahalle_heterojen=heter,
        mahalle_ilan_n=mah_n,
        segment_duzeltme=k_seg,
        segment_etiketi=seg_label,
        trend_yillik_nominal_pct=_proj["trend_yillik_nominal_pct"],
        projeksiyon_12ay_tlm2=_proj["projeksiyon_12ay_tlm2"],
        projeksiyon_24ay_tlm2=_proj["projeksiyon_24ay_tlm2"],
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
