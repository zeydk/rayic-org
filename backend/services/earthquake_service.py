import os
import json
import math
from typing import Dict, Any, List, Optional, Tuple

# ---------------------------------------------------------------------------
# District soil amplification factors (from IBB Mikrobölgeleme reports).
# ---------------------------------------------------------------------------
DISTRICT_AMPLIFICATIONS = {
    "Adalar": 1.5, "Arnavutköy": 1.0, "Ataşehir": 1.2, "Avcılar": 1.5,
    "Bağcılar": 1.3, "Bahçelievler": 1.3, "Bakırköy": 1.5, "Başakşehir": 1.1,
    "Bayrampaşa": 1.2, "Beşiktaş": 1.0, "Beykoz": 1.0, "Beylikdüzü": 1.4,
    "Beyoğlu": 1.2, "Büyükçekmece": 1.4, "Çatalca": 1.1, "Çekmeköy": 1.0,
    "Esenler": 1.3, "Esenyurt": 1.4, "Eyüpsultan": 1.1, "Fatih": 1.2,
    "Gaziosmanpaşa": 1.2, "Güngören": 1.3, "Kadıköy": 1.2, "Kağıthane": 1.2,
    "Kartal": 1.3, "Küçükçekmece": 1.4, "Maltepe": 1.3, "Pendik": 1.3,
    "Sancaktepe": 1.0, "Sarıyer": 1.0, "Şile": 1.0, "Şişli": 1.2,
    "Sultanbeyli": 1.1, "Sultangazi": 1.1, "Tuzla": 1.2, "Ümraniye": 1.0,
    "Üsküdar": 1.2, "Zeytinburnu": 1.5
}


def get_district_amplification(district: str) -> float:
    d_clean = (district or "").strip().capitalize()
    return DISTRICT_AMPLIFICATIONS.get(d_clean, 1.2)  # Default 1.2 if not found


# ---------------------------------------------------------------------------
# Geometry helpers.
# ---------------------------------------------------------------------------
def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _point_to_segment_km(plat, plng, alat, alng, blat, blng) -> float:
    """Distance (km) from a point to segment A-B via local equirectangular projection."""
    latr = math.radians((alat + blat) / 2.0)
    kx = 111.320 * math.cos(latr)
    ky = 110.574
    px, py = (plng - alng) * kx, (plat - alat) * ky
    bx, by = (blng - alng) * kx, (blat - alat) * ky
    seg2 = bx * bx + by * by
    t = 0.0 if seg2 == 0 else max(0.0, min(1.0, (px * bx + py * by) / seg2))
    dx, dy = px - t * bx, py - t * by
    return math.sqrt(dx * dx + dy * dy)


def _min_distance_to_polylines(lat: float, lng: float, polylines: List[List[Tuple[float, float]]]) -> float:
    """`polylines` is a list of [(lat,lng), ...] vertex lists. Returns min km distance."""
    best = 1e9
    for line in polylines:
        for i in range(len(line) - 1):
            a, b = line[i], line[i + 1]
            d = _point_to_segment_km(lat, lng, a[0], a[1], b[0], b[1])
            if d < best:
                best = d
    return best


# ---------------------------------------------------------------------------
# Main Marmara Fault geometry (real segments: Tekirdağ, Central Marmara,
# Kumburgaz, Avcılar, Çınarcık) loaded from data/marmara_fault.json.
# ---------------------------------------------------------------------------
def _load_fault_polylines() -> List[List[Tuple[float, float]]]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "marmara_fault.json")
    lines: List[List[Tuple[float, float]]] = []
    try:
        with open(path, encoding="utf-8") as f:
            segs = json.load(f)
        for seg in segs:
            # stored as [lng, lat]; convert to (lat, lng)
            lines.append([(c[1], c[0]) for c in seg["coords"]])
    except Exception:
        # Fallback: a coarse straight approximation of the northern NAF branch.
        lines.append([(40.88, 27.0), (40.82, 28.0), (40.80, 28.6), (40.75, 29.0), (40.72, 29.35)])
    return lines


_FAULT_POLYLINES = _load_fault_polylines()


def distance_to_fault_km(lat: float, lng: float) -> float:
    """Closest distance (km) from a coordinate to the Main Marmara Fault."""
    return _min_distance_to_polylines(lat, lng, _FAULT_POLYLINES)


# ---------------------------------------------------------------------------
# Ground motion: scenario PGA via Campbell (1997) horizontal rock attenuation,
# scaled by local soil amplification.
# ---------------------------------------------------------------------------
def scenario_pga_g(distance_km: float, amplification: float = 1.0, magnitude: float = 7.5) -> float:
    """Peak Ground Acceleration (g) for a scenario earthquake.

    Campbell (1997) empirical relation for horizontal PGA on soft rock, then
    multiplied by the site amplification factor. Returned value is clamped to a
    physically plausible range.
    """
    R = max(distance_km, 3.0)  # avoid singularity in the near field
    ln_pga_rock = (
        -3.512
        + 0.904 * magnitude
        - 1.328 * math.log(math.sqrt(R * R + (0.149 * math.exp(0.647 * magnitude)) ** 2))
    )
    pga = math.exp(ln_pga_rock) * amplification
    return max(0.02, min(pga, 1.2))


def pga_to_mmi(pga_g: float) -> float:
    """Instrumental Modified Mercalli Intensity from PGA (Wald et al., 1999)."""
    accel = max(pga_g, 1e-4) * 981.0  # cm/s^2
    mmi = 3.66 * math.log10(accel) - 1.66
    return max(1.0, min(12.0, mmi))


def compute_mmi(magnitude: float, distance_km: float, amplification: float = 1.0) -> float:
    """Backward-compatible MMI: derived consistently from the scenario PGA."""
    return pga_to_mmi(scenario_pga_g(distance_km, amplification, magnitude))


# ---------------------------------------------------------------------------
# Coastline geometry -> tsunami / coastal-flood exposure (İBB MeTHuVA logic).
# Coarse İstanbul Marmara + Bosphorus shoreline (lat, lng).
# ---------------------------------------------------------------------------
_COASTLINE: List[Tuple[float, float]] = [
    (40.970, 28.58), (40.970, 28.63), (40.975, 28.72), (40.970, 28.77), (40.965, 28.80),
    (40.972, 28.87), (40.990, 28.90), (40.998, 28.95), (41.006, 28.98), (41.020, 28.985),
    (41.040, 29.005), (41.050, 29.03), (41.077, 29.043), (41.090, 29.05), (41.130, 29.05),
    (41.170, 29.05), (41.170, 29.09), (41.130, 29.10), (41.060, 29.06), (41.020, 29.02),
    (41.000, 29.01), (40.990, 29.02), (40.972, 29.045), (40.963, 29.06), (40.950, 29.10),
    (40.925, 29.13), (40.905, 29.16), (40.890, 29.19), (40.870, 29.23), (40.840, 29.30),
]


def distance_to_coast_km(lat: float, lng: float) -> float:
    return _min_distance_to_polylines(lat, lng, [_COASTLINE])


def fetch_elevation_m(lat: float, lng: float) -> Optional[float]:
    """Real ground elevation (m) from the open-meteo elevation API. None on failure."""
    try:
        import requests
        url = "https://api.open-meteo.com/v1/elevation"
        resp = requests.get(url, params={"latitude": lat, "longitude": lng}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            vals = data.get("elevation")
            if vals:
                return float(vals[0])
    except Exception:
        pass
    return None


def _norm_tr_ascii(s: str) -> str:
    """Uppercase + Turkish->ASCII fold, matching the MeTHuVA table keys."""
    s = (s or "").strip().upper().replace("İ", "I")
    out = [{"Ç": "C", "Ğ": "G", "Ö": "O", "Ş": "S", "Ü": "U", "Â": "A"}.get(ch, ch) for ch in s]
    return " ".join("".join(out).split())


def _load_tsunami_lookup() -> Dict[str, Dict[str, Dict[str, float]]]:
    """İBB/METU MeTHuVA 2018 per-mahalle CMN (seismic Central Marmara Fault)
    tsunami inundation results extracted from the official report."""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "tsunami_methuva.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_TSUNAMI = _load_tsunami_lookup()


def estimate_tsunami_risk(district: str, neighborhood: str,
                          elevation_m: Optional[float], coast_dist_km: float):
    """Tsunami / coastal-flood exposure.

    Primary source: the İBB MeTHuVA (2018) modelled inundation results — actual
    maximum water depth and flooded-area share per mahalle for the Central
    Marmara Fault (CMN) seismic scenario. Falls back to a real elevation +
    coastal-proximity heuristic for mahalles the model did not flood / list.

    Returns (label, max_depth_m, flood_pct). depth/pct are the modelled MeTHuVA
    values (0.0 when the mahalle is not in a modelled inundation zone).
    """
    rec = _TSUNAMI.get(_norm_tr_ascii(district), {}).get(_norm_tr_ascii(neighborhood))
    if rec:
        depth = float(rec.get("max_depth", 0.0))
        pct = float(rec.get("flood_pct", 0.0))
        if depth >= 3.0 or pct >= 10.0:
            return f"Yüksek (MeTHuVA: ~{depth:.1f} m Su Baskını)", depth, pct
        if depth >= 1.0:
            return f"Orta (MeTHuVA: ~{depth:.1f} m Kısmi Su Baskını)", depth, pct
        return f"Düşük-Orta (MeTHuVA: ~{depth:.1f} m Sınırlı)", depth, pct

    # Not in the modelled inundation list -> low risk, but guard name mismatches
    # for genuinely shore-front, very-low parcels via real geography.
    if coast_dist_km <= 0.5 and (elevation_m is not None and elevation_m <= 6):
        return "Orta (Kıyı Şeridi - Yerel Su Baskını Olası)", 1.0, 0.0
    return "Düşük (MeTHuVA: Su Baskını Öngörülmüyor)", 0.0, 0.0


# ---------------------------------------------------------------------------
# Microzonation ground (site) class.
# Base = dominant site class per district from the İBB Mikrobölgeleme reports;
# refined per-parcel with real elevation + coastal proximity (coastal alluvium
# is weaker, bedrock uplands are firmer).
# ---------------------------------------------------------------------------
_GC_ORDER = ["Z1", "Z2", "Z3", "Z4"]
_GC_LABEL = {
    "Z1": "Z1 (Çok Sağlam Kaya Zemin)",
    "Z2": "Z2 (Sağlam Zemin)",
    "Z3": "Z3 (Orta-Zayıf Zemin)",
    "Z4": "Z4 (Zayıf / Alüvyon Zemin)",
}
DISTRICT_GROUND_CLASS = {
    "Avcılar": "Z4", "Küçükçekmece": "Z4", "Bakırköy": "Z3", "Zeytinburnu": "Z3",
    "Bahçelievler": "Z3", "Bağcılar": "Z3", "Esenyurt": "Z3", "Beylikdüzü": "Z3",
    "Büyükçekmece": "Z3", "Güngören": "Z3", "Fatih": "Z2", "Esenler": "Z2",
    "Bayrampaşa": "Z2", "Gaziosmanpaşa": "Z2", "Sultangazi": "Z2", "Kağıthane": "Z2",
    "Şişli": "Z2", "Beyoğlu": "Z2", "Eyüpsultan": "Z2", "Kadıköy": "Z2",
    "Ataşehir": "Z2", "Ümraniye": "Z2", "Maltepe": "Z2", "Kartal": "Z3",
    "Pendik": "Z3", "Tuzla": "Z2", "Sancaktepe": "Z2", "Sultanbeyli": "Z2",
    "Başakşehir": "Z2", "Arnavutköy": "Z2", "Üsküdar": "Z2", "Adalar": "Z2",
    "Çatalca": "Z2", "Beşiktaş": "Z1", "Sarıyer": "Z1", "Beykoz": "Z1",
    "Çekmeköy": "Z1", "Şile": "Z1",
}


def estimate_ground_class(district: str, elevation_m: Optional[float], coast_dist_km: float) -> Tuple[str, str]:
    """Returns (code, label) e.g. ('Z3', 'Z3 (Orta-Zayıf Zemin)')."""
    base = DISTRICT_GROUND_CLASS.get((district or "").strip().capitalize(), "Z2")
    idx = _GC_ORDER.index(base)
    if elevation_m is not None:
        if elevation_m <= 8 and coast_dist_km <= 2.0:
            idx = min(3, idx + 1)   # coastal alluvium / reclaimed land -> weaker
        elif elevation_m >= 90:
            idx = max(0, idx - 1)   # bedrock uplands -> firmer
    code = _GC_ORDER[idx]
    return code, _GC_LABEL[code]


def ground_class_to_n(ground_code: str) -> int:
    """Representative SPT-N used as a liquefaction input for the site class."""
    return {"Z1": 25, "Z2": 15, "Z3": 8, "Z4": 4}.get(ground_code, 15)


# ---------------------------------------------------------------------------
# LIQUEFACTION (TBDY Ek 16B) — unchanged engineering formulation.
# ---------------------------------------------------------------------------
def _hesapla_C_N(sigma: float) -> float:
    return min(9.78 * math.sqrt(1.0 / max(sigma, 0.1)), 1.70)


def _hesapla_alfa_beta(IDI: float):
    if IDI <= 5:
        return 0.0, 1.0
    elif IDI <= 35:
        return math.exp(1.76 - 190.0 / (IDI ** 2)), 0.99 + (IDI ** 1.5) / 1000.0
    else:
        return 5.0, 1.2


def _hesapla_CRR_M7_5(N1_60f: float) -> float:
    if N1_60f >= 34:
        return 10.0
    return max(1.0 / (34.0 - N1_60f) + N1_60f / 135.0 + 50.0 / ((10.0 * N1_60f + 45.0) ** 2) - 1.0 / 200.0, 0.001)


def _hesapla_r_d(z: float) -> float:
    if z <= 9.15:
        return 1.0 - 0.00765 * z
    elif z <= 23.0:
        return 1.174 - 0.0267 * z
    elif z <= 30.0:
        return 0.744 - 0.008 * z
    else:
        return 0.50


def calculate_liquefaction_safety_factor(
    depth_m: float = 6.0,
    n_ham: float = 15,
    idi_percent: float = 10,
    gamma: float = 19.0,
    gwl: float = 2.0,
    magnitude: float = 7.5,
    pga: float = 0.4
) -> float:
    """Liquefaction Factor of Safety (FS) for a single soil layer using TBDY Ek 16B."""
    if depth_m <= gwl:
        return 10.0  # No liquefaction above groundwater level

    sigma_v = depth_m * gamma
    sigma_v_eff = (gwl * gamma) + ((depth_m - gwl) * (gamma - 9.81))

    C_N = _hesapla_C_N(sigma_v_eff)
    C_R, C_S, C_B, C_E = 0.95, 1.0, 1.0, 0.88
    N1_60 = n_ham * C_N * C_R * C_S * C_B * C_E

    alfa, beta = _hesapla_alfa_beta(idi_percent)
    N1_60f = alfa + beta * N1_60

    CRR_75 = _hesapla_CRR_M7_5(N1_60f)
    MSF = 10 ** 2.24 / magnitude ** 2.56
    CRR = CRR_75 * MSF

    r_d = _hesapla_r_d(depth_m)
    CSR = 0.65 * pga * (sigma_v / sigma_v_eff) * r_d

    FS = CRR / CSR if CSR > 0 else 10.0
    return round(FS, 2)


# ---------------------------------------------------------------------------
# Building damage-state probabilities (fragility-based, localized with real
# İBB "Olası Deprem Kayıp Tahminleri" mahalle damage-severity signatures).
# ---------------------------------------------------------------------------
def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def calculate_damage_probabilities(
    base_probs: Dict[str, float],
    building_age_years: int,
    num_floors: int,
    pga: float
) -> Dict[str, float]:
    """Probability of each damage state for THIS building under the scenario PGA.

    HAZUS-style multi-state fragility: four lognormal capacity curves give the
    exceedance probabilities P(DS ≥ slight/moderate/extensive/complete). The
    curve medians depend on the seismic-code era (building age) and height, and
    are further scaled by the REAL per-mahalle vulnerability signature from the
    İBB earthquake loss scenario (weaker building stock → lower medians → more
    severe damage). Differencing the exceedance curves yields the five states.
    Returns percentages (0-100): hasarsiz, hafif, orta, agir, cok_agir (sum≈100).
    """
    age = building_age_years if building_age_years is not None else 20
    floors = num_floors if num_floors is not None else 5

    # 1) Median PGA (g) thresholds for [slight, moderate, extensive, complete]
    #    by seismic-code era.
    if age > 25:        # pre-2000 (before modern seismic codes)
        medians = [0.10, 0.16, 0.28, 0.45]
    elif age > 5:       # 2000-2018
        medians = [0.14, 0.22, 0.40, 0.65]
    else:               # 2018+ (TBDY 2018)
        medians = [0.20, 0.32, 0.55, 0.90]

    # Height: low-rise is stiffer/less fragile, high-rise more fragile.
    if floors <= 3:
        hf = 1.15
    elif floors <= 7:
        hf = 1.00
    else:
        hf = 0.82
    medians = [m * hf for m in medians]

    # 2) Localise with the real İBB mahalle damage-severity signature.
    cok = float(base_probs.get("cok_agir_prob", base_probs.get("cok_agir", 2.0)))
    agir = float(base_probs.get("agir_prob", base_probs.get("agir", 6.0)))
    orta = float(base_probs.get("orta_prob", base_probs.get("orta", 25.0)))
    hafif = float(base_probs.get("hafif_prob", base_probs.get("hafif", 67.0)))
    tot = cok + agir + orta + hafif
    if tot <= 0:
        cok, agir, orta, tot = 2.0, 6.0, 25.0, 100.0
    severity_index = (cok * 1.0 + agir * 0.6 + orta * 0.3) / tot
    # ~0.12 is a typical İstanbul mahalle; weaker (higher) => scale medians down.
    vuln_scale = min(1.30, max(0.80, (0.12 / max(severity_index, 0.03)) ** 0.5))
    medians = [m * vuln_scale for m in medians]

    # 3) Lognormal exceedance probabilities, then difference into 5 states.
    beta = 0.60
    exc = [_normal_cdf(math.log(max(pga, 1e-3) / m) / beta) for m in medians]
    hasarsiz = 1.0 - exc[0]
    hafif_p = exc[0] - exc[1]
    orta_p = exc[1] - exc[2]
    agir_p = exc[2] - exc[3]
    cok_p = exc[3]

    return {
        "cok_agir": round(cok_p * 100.0, 2),
        "agir": round(agir_p * 100.0, 2),
        "orta": round(orta_p * 100.0, 2),
        "hafif": round(hafif_p * 100.0, 2),
        "hasarsiz": round(hasarsiz * 100.0, 2),
    }
