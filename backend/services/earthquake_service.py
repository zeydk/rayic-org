import math
from typing import Dict, Any

# District soil amplification factors from IBB Mikrobölgeleme reports
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
    # Normalize for matching
    d_clean = district.capitalize().strip()
    return DISTRICT_AMPLIFICATIONS.get(d_clean, 1.2) # Default 1.2 if not found

def compute_mmi(magnitude: float, distance_km: float, amplification: float = 1.0) -> float:
    """
    Computes Modified Mercalli Intensity (MMI) based on magnitude, distance and local soil amplification.
    Based on olasi.istanbul empirical attenuation relation.
    """
    safe_distance = max(distance_km, 1.0)
    base_mmi = 1.5 * magnitude - 3.0 * math.log10(safe_distance)
    mmi = base_mmi * amplification
    # Clamp MMI between 1.0 and 12.0 for reporting
    return max(1.0, min(12.0, round(mmi, 1)))


# --- LIQUEFACTION (TBDY EK 16B) ALGORITHMS ---

def _hesapla_C_N(sigma: float) -> float:
    return min(9.78 * math.sqrt(1.0 / max(sigma, 0.1)), 1.70)

def _hesapla_alfa_beta(IDI: float):
    if IDI <= 5: 
        return 0.0, 1.0
    elif IDI <= 35: 
        return math.exp(1.76 - 190.0/(IDI**2)), 0.99 + (IDI**1.5)/1000.0
    else: 
        return 5.0, 1.2

def _hesapla_CRR_M7_5(N1_60f: float) -> float:
    if N1_60f >= 34: 
        return 10.0
    return max(1.0/(34.0-N1_60f) + N1_60f/135.0 + 50.0/((10.0*N1_60f+45.0)**2) - 1.0/200.0, 0.001)

def _hesapla_r_d(z: float) -> float:
    if z <= 9.15: 
        return 1.0 - 0.00765*z
    elif z <= 23.0: 
        return 1.174 - 0.0267*z
    elif z <= 30.0: 
        return 0.744 - 0.008*z
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
    """
    Calculates Liquefaction Factor of Safety (FS) for a single soil layer using TBDY Ek 16B.
    """
    if depth_m <= gwl:
        return 10.0 # No liquefaction above groundwater level
    
    # Calculate stresses
    sigma_v = depth_m * gamma
    sigma_v_eff = (gwl * gamma) + ((depth_m - gwl) * (gamma - 9.81))
    
    # Corrections
    C_N = _hesapla_C_N(sigma_v_eff)
    C_R, C_S, C_B, C_E = 0.95, 1.0, 1.0, 0.88 # Standard defaults
    N1_60 = n_ham * C_N * C_R * C_S * C_B * C_E
    
    # Fines content correction
    alfa, beta = _hesapla_alfa_beta(idi_percent)
    N1_60f = alfa + beta * N1_60
    
    # CRR & CSR
    CRR_75 = _hesapla_CRR_M7_5(N1_60f)
    MSF = 10**2.24 / magnitude**2.56 # Magnitude Scaling Factor
    CRR = CRR_75 * MSF
    
    r_d = _hesapla_r_d(depth_m)
    CSR = 0.65 * pga * (sigma_v / sigma_v_eff) * r_d
    
    FS = CRR / CSR if CSR > 0 else 10.0
    return round(FS, 2)


# --- IBB (HAZUS-based) BUILDING DAMAGE PROBABILITY ALGORITHM ---

def calculate_damage_probabilities(
    base_probs: Dict[str, float],
    building_age_years: int,
    num_floors: int,
    pga: float
) -> Dict[str, float]:
    """
    Scales the neighborhood base damage probabilities according to specific building typology
    using KOERI / HAZUS capacity spectrum modifiers.
    Returns probabilities in percentages: hafif, orta, agir, cok_agir, hasarsiz.
    """
    # 1. Typology Classifications
    if building_age_years > 25: # pre-2000 (Before the 1998/2000 seismic codes)
        code_level = "Pre-code"
        vuln_modifier = 2.0
    elif building_age_years > 5: # 2000-2018 (2007 seismic code)
        code_level = "Moderate-code"
        vuln_modifier = 0.8
    else: # 2018+ (2018 TBDY seismic code)
        code_level = "High-code"
        vuln_modifier = 0.2
        
    # 2. Height Classifications
    if num_floors <= 3: # Low-rise
        height_modifier = 0.8
    elif num_floors <= 7: # Mid-rise
        height_modifier = 1.2
    else: # High-rise
        height_modifier = 1.6
        
    # 3. PGA Factor (baseline PGA is around 0.3g in Istanbul, so higher means more damage)
    pga_modifier = max(0.5, min(2.5, pga / 0.3))
    
    # Total Vulnerability Shift
    shift = vuln_modifier * height_modifier * pga_modifier
    
    # Extract base probabilities (default fallbacks if missing)
    c = float(base_probs.get("cok_agir", 2.0))
    a = float(base_probs.get("agir", 5.0))
    o = float(base_probs.get("orta", 15.0))
    h = float(base_probs.get("hafif", 35.0))
    hasarsiz = max(0.0, 100.0 - (c + a + o + h))
    
    # Apply exponential shifts to the severe damages (non-linear scaling)
    c_new = c * (shift ** 2)
    a_new = a * (shift ** 1.5)
    o_new = o * (shift ** 1.2)
    h_new = h * (shift ** 0.8)
    
    # Re-normalize if they exceed realistic bounds
    total_damage = c_new + a_new + o_new + h_new
    if total_damage >= 100.0:
        scale = 99.9 / total_damage
        c_new *= scale
        a_new *= scale
        o_new *= scale
        h_new *= scale
        
    hasarsiz_new = 100.0 - (c_new + a_new + o_new + h_new)
    
    return {
        "cok_agir": round(c_new, 2),
        "agir": round(a_new, 2),
        "orta": round(o_new, 2),
        "hafif": round(h_new, 2),
        "hasarsiz": round(hasarsiz_new, 2)
    }
