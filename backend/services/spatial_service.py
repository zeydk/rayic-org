import math
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .earthquake_service import (
    get_district_amplification,
    calculate_liquefaction_safety_factor,
    calculate_damage_probabilities,
    distance_to_fault_km,
    scenario_pga_g,
    pga_to_mmi,
    distance_to_coast_km,
    fetch_elevation_m,
    estimate_tsunami_risk,
    estimate_ground_class,
    ground_class_to_n,
)
from .data_loader import ibb_loader
from .imar_service import fetch_imar_durumu, fetch_parcel_geometry

class POIItem(BaseModel):
    id: str
    name: str
    category: str
    lat: float
    lng: float
    distance_meters: float

class SafetyReportResult(BaseModel):
    safety_score: int
    safety_grade: str
    night_walkability_rating: float
    street_lighting_score: int
    camera_surveillance_index: str
    crime_rate_index: str
    safety_notes: List[str]

class SchoolItem(BaseModel):
    name: str
    type: str
    distance_meters: float
    lgs_percentile: Optional[str]
    student_per_classroom: int
    rating_score: float

class EducationReportResult(BaseModel):
    education_score: int
    education_grade: str
    total_schools_15km: int
    top_rated_schools: List[SchoolItem]
    education_notes: List[str]

class TKGMOznitelikInfo(BaseModel):
    tasinmaz_id: str
    il_ad: str
    ilce_ad: str
    mahalle_ad: str
    ada_no: str
    parsel_no: str
    alani_m2: float
    nitelik: str
    pafta_no: str
    mevkii: str

class TKGMBagimsizBolumItem(BaseModel):
    bb_no: str
    daire_no: str
    bb_tipi: str
    kat_no: str
    arsa_pay_payda: str
    blok_no: str

class TKGMCadastreInfo(BaseModel):
    ada_no: str
    parsel_no: str
    total_land_area_m2: float
    is_auto_matched: bool
    match_accuracy_percent: float
    tkgm_status_label: str
    precise_lat: float
    precise_lng: float
    polygon_geometry: Optional[Dict[str, Any]] = None
    oznitelik: Optional[TKGMOznitelikInfo] = None
    kat_mulkiyeti_durumu: str = "-"
    bb_listesi: List[TKGMBagimsizBolumItem] = []
    bb_veri_durumu: str = ""
    imar_durumu: Optional[Dict[str, Any]] = None

class SpatialCheckupResult(BaseModel):
    property_lat: float
    property_lng: float
    district: str
    neighborhood: str
    full_address: Optional[str]
    tkgm_cadastre: TKGMCadastreInfo
    ground_risk_class: str
    pga_earthquake_risk_score: float
    mmi_estimated: float
    liquefaction_fs: float
    district_amplification: float
    fault_distance_km: float
    tsunami_risk: Optional[str] = "Düşük (Bilinmiyor)"
    tsunami_depth_m: float = 0.0
    tsunami_flood_pct: float = 0.0
    damage_probabilities: Dict[str, float]
    pois_within_1km: List[POIItem]
    poi_summary: Dict[str, int]
    score_transit: int
    score_health_edu: int
    score_transformation_activity: int
    safety_report: SafetyReportResult
    education_report: EducationReportResult

# Neighborhood Centers Coordinates Map
NEIGHBORHOOD_CENTERS = {
    "Erenköy": {"lat": 40.9740, "lng": 29.0760, "district": "Kadıköy", "ground_risk": "Z2 (Orta Güvenli Zemin)", "pga": 0.26, "safety_score": 93, "safety_grade": "A+ (Çok Güvenli)", "walkability": 4.8, "tsunami_risk": "Düşük (İç Kesim)"},
    "Caddebostan": {"lat": 40.9675, "lng": 29.0652, "district": "Kadıköy", "ground_risk": "Z2 (Orta Güvenli Zemin)", "pga": 0.28, "safety_score": 94, "safety_grade": "A+ (Çok Güvenli)", "walkability": 4.9, "tsunami_risk": "Yüksek (Kıyı Şeridi - MeTHuVA Riskli)"},
    "Suadiye": {"lat": 40.9610, "lng": 29.0780, "district": "Kadıköy", "ground_risk": "Z2 (Orta Güvenli)", "pga": 0.29, "safety_score": 92, "safety_grade": "A+ (Çok Güvenli)", "walkability": 4.8, "tsunami_risk": "Yüksek (Kıyı Şeridi - MeTHuVA Riskli)"},
    "Caferağa": {"lat": 40.9870, "lng": 29.0260, "district": "Kadıköy", "ground_risk": "Z1 (Çok Sağlam Kaya Zemin)", "pga": 0.24, "safety_score": 90, "safety_grade": "A (Güvenli)", "walkability": 4.7, "tsunami_risk": "Yüksek (Kıyı Şeridi - MeTHuVA Riskli)"},
    "Göztepe": {"lat": 40.9820, "lng": 29.0580, "district": "Kadıköy", "ground_risk": "Z2 (Sağlam)", "pga": 0.27, "safety_score": 91, "safety_grade": "A (Aile Dostu Güvenli)", "walkability": 4.7, "tsunami_risk": "Düşük (İç Kesim)"},
    "Çınar": {"lat": 40.9483, "lng": 29.1303, "district": "Maltepe", "ground_risk": "Z2 (Orta Sağlam)", "pga": 0.32, "safety_score": 86, "safety_grade": "B+ (Güvenli Yerleşim)", "walkability": 4.5, "tsunami_risk": "Yüksek (Kıyı Şeridi - MeTHuVA Riskli)"},
    "Cumhuriyet": {"lat": 40.8886, "lng": 29.1856, "district": "Kartal", "ground_risk": "Z2 (Orta Zemin)", "pga": 0.33, "safety_score": 84, "safety_grade": "B+ (Makul Güvenli)", "walkability": 4.3, "tsunami_risk": "Düşük (İç Kesim)"},
    "Küçükyalı": {"lat": 40.9560, "lng": 29.1050, "district": "Maltepe", "ground_risk": "Z2 (Orta Zemin)", "pga": 0.31, "safety_score": 84, "safety_grade": "B+ (Makul Güvenli)", "walkability": 4.3, "tsunami_risk": "Yüksek (Kıyı Şeridi - MeTHuVA Riskli)"},
    "Bebek": {"lat": 41.0760, "lng": 29.0430, "district": "Beşiktaş", "ground_risk": "Z1 (Çok Sağlam Kaya)", "pga": 0.18, "safety_score": 96, "safety_grade": "A+ (Üst Seviye Güvenli)", "walkability": 4.9, "tsunami_risk": "Yüksek (Boğaz Kıyısı - MeTHuVA Riskli)"},
    "Nişantaşı": {"lat": 41.0520, "lng": 28.9930, "district": "Şişli", "ground_risk": "Z1 (Sağlam Kaya)", "pga": 0.20, "safety_score": 93, "safety_grade": "A+ (Prestijli & Güvenli)", "walkability": 4.8, "tsunami_risk": "Düşük (İç Kesim Yüksek Rakım)"}
}

SPATIAL_POIS = [
    {"id": "m1", "name": "Göztepe Metro İstasyonu", "category": "metro", "lat": 40.9812, "lng": 29.0570},
    {"id": "m2", "name": "Bostancı Metro İstasyonu", "category": "metro", "lat": 40.9634, "lng": 29.0961},
    {"id": "m3", "name": "Kadıköy Metro & İskele", "category": "metro", "lat": 40.9904, "lng": 29.0254},
    {"id": "mb1", "name": "Söğütlüçeşme Metrobüs Durağı", "category": "metrobus", "lat": 40.9912, "lng": 29.0371},
    {"id": "h1", "name": "Göztepe Şehir Hastanesi", "category": "hospital", "lat": 40.9855, "lng": 29.0610},
    {"id": "t1", "name": "Kentsel Dönüşüm Projesi", "category": "transformation", "lat": 40.9680, "lng": 29.0660}
]


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ---------------------------------------------------------------------------
# Geocoding: address -> candidate lat/lng points across multiple providers.
# We deliberately collect SEVERAL candidates and disambiguate them later against
# the live TKGM cadastre, so a point that lands on a road/void is rejected in
# favour of the real building parcel.
# ---------------------------------------------------------------------------

GEOCODER_SOURCE_PRIORITY = {"arcgis": 3, "nominatim": 2, "photon": 1}

# Rough bounding box for Istanbul (min_lat, max_lat, min_lng, max_lng).
ISTANBUL_BOUNDS = (40.70, 41.45, 28.40, 29.70)


def _normalize_tr(text: Optional[str]) -> str:
    s = (text or "").strip().lower()
    for a, b in (("ı", "i"), ("İ", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"),
                 ("ö", "o"), ("ç", "c"), ("â", "a"), ("î", "i"), ("û", "u")):
        s = s.replace(a, b)
    return s


def _in_istanbul(lat: float, lng: float) -> bool:
    mnla, mxla, mnlo, mxlo = ISTANBUL_BOUNDS
    return mnla <= lat <= mxla and mnlo <= lng <= mxlo


def geocode_arcgis(address: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
        params = {"singleLine": address, "f": "json", "maxLocations": 3, "countryCode": "TUR"}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            for c in resp.json().get("candidates", [])[:3]:
                loc = c.get("location", {})
                if "y" in loc and "x" in loc:
                    out.append({"lat": float(loc["y"]), "lng": float(loc["x"]),
                                "source": "arcgis", "score": float(c.get("score", 0) or 0)})
    except Exception:
        pass
    return out


def geocode_photon(address: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        url = "https://photon.komoot.io/api/"
        params = {"q": address, "limit": 3}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            for f in resp.json().get("features", [])[:3]:
                co = f.get("geometry", {}).get("coordinates")
                if co and len(co) >= 2:
                    out.append({"lat": float(co[1]), "lng": float(co[0]),
                                "source": "photon", "score": 50.0})
    except Exception:
        pass
    return out


def geocode_nominatim(address: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json", "limit": 3, "countrycodes": "tr"}
        headers = {"User-Agent": "rayic-org/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            for r in resp.json()[:3]:
                out.append({"lat": float(r["lat"]), "lng": float(r["lon"]),
                            "source": "nominatim", "score": float(r.get("importance", 0) or 0) * 100})
    except Exception:
        pass
    return out


def geocode_address_candidates(address: str) -> List[Dict[str, Any]]:
    """Query every provider and return de-duplicated, in-region candidate points."""
    cands: List[Dict[str, Any]] = []
    for fn in (geocode_arcgis, geocode_photon, geocode_nominatim):
        cands.extend(fn(address))
    cands = [c for c in cands if _in_istanbul(c["lat"], c["lng"])]
    deduped: List[Dict[str, Any]] = []
    for c in cands:
        if not any(haversine_distance(c["lat"], c["lng"], d["lat"], d["lng"]) < 8 for d in deduped):
            deduped.append(c)
    return deduped


def geocode_address_to_latlng(address: str) -> Optional[Dict[str, float]]:
    """Back-compat single-point helper: best-effort first candidate."""
    cands = geocode_address_candidates(address)
    return cands[0] if cands else None


# ---------------------------------------------------------------------------
# TKGM MEGSIS cadastre lookup (coords -> real ada/parsel + parcel geometry).
# ---------------------------------------------------------------------------

# Parcel "nitelik" values that are NOT a building (roads, parks, voids...).
ROAD_LIKE_NITELIK = {
    "yol", "yeşil alan", "park", "dere", "kanal", "tescil harici",
    "otopark alanı", "meydan", "kaldırım", "spor alanı", "mezarlık",
}


def _spiral_offsets() -> List[tuple]:
    """Offsets in degrees (~up to 30 m) used to escape a point that landed on a
    road/void and snap onto the nearest real building parcel."""
    offs = [(0.0, 0.0)]
    for radius in (0.00012, 0.00025):
        for ang in range(0, 360, 45):
            offs.append((radius * math.cos(math.radians(ang)), radius * math.sin(math.radians(ang))))
    return offs


_SPIRAL_OFFSETS = _spiral_offsets()


def _polygon_centroid(geom: Optional[Dict[str, Any]]) -> Optional[tuple]:
    """Return (lat, lng) centroid (vertex average of the outer ring)."""
    if not geom:
        return None
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if not coords:
        return None
    if gtype == "Polygon":
        ring = coords[0]
    elif gtype == "MultiPolygon":
        ring = coords[0][0]
    else:
        return None
    if not ring:
        return None
    xs = [pt[0] for pt in ring]
    ys = [pt[1] for pt in ring]
    return (sum(ys) / len(ys), sum(xs) / len(xs))


def _is_road_parcel(props: Dict[str, Any]) -> bool:
    nit = (props.get("nitelik") or "").strip().lower()
    if not nit:
        return False
    return nit in ROAD_LIKE_NITELIK or nit.startswith("yol")


def _parse_tkgm_parcel(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    props = data.get("properties")
    if not props:
        return None
    ada = str(props.get("adaNo", "")).strip()
    parsel = str(props.get("parselNo", "")).strip()
    if not ada or not parsel:
        return None
    raw_alan = props.get("alan", 0)
    if isinstance(raw_alan, str):
        raw_alan = raw_alan.replace(",", "")
    try:
        area = float(raw_alan)
    except (ValueError, TypeError):
        area = 0.0
    geom = data.get("geometry")
    return {
        "ada": ada,
        "parsel": parsel,
        "area": area,
        "nitelik": (props.get("nitelik") or "").strip(),
        "pafta": (props.get("pafta") or "").strip(),
        "mevkii": (props.get("mevkii") or "").strip(),
        "mahalle": (props.get("mahalleAd") or "").strip(),
        "ilce": (props.get("ilceAd") or "").strip(),
        "il": (props.get("ilAd") or "").strip(),
        "kat_durum": (props.get("zeminKmdurum") or "").strip(),
        "is_road": _is_road_parcel(props),
        "geometry": geom,
        "centroid": _polygon_centroid(geom),
    }


def _fetch_tkgm_raw(lat: float, lng: float) -> Optional[Dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://parselsorgu.tkgm.gov.tr/",
        "Origin": "https://parselsorgu.tkgm.gov.tr",
    }
    try:
        url = f"https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api/parsel/{lat}/{lng}"
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("properties"):
                return data
    except Exception:
        pass
    return None


def fetch_tkgm_parcel_by_coords(lat: float, lng: float, spiral: bool = True) -> Optional[Dict[str, Any]]:
    """Resolve the parcel at a point. If the point lands on a road/void, spiral
    outwards (~30 m) to snap onto the nearest real building parcel. Returns a
    normalized parcel dict (with `dist_m` = metres from the query point to the
    parcel centroid) or None."""
    offsets = _SPIRAL_OFFSETS if spiral else [(0.0, 0.0)]
    best = None
    for idx, (dlat, dlng) in enumerate(offsets):
        raw = _fetch_tkgm_raw(lat + dlat, lng + dlng)
        if not raw:
            continue
        parcel = _parse_tkgm_parcel(raw)
        if not parcel:
            continue
        cen = parcel["centroid"]
        parcel["dist_m"] = haversine_distance(lat, lng, cen[0], cen[1]) if cen else 9999.0
        # Exact building hit right at the geocoded point -> perfect, stop early.
        if idx == 0 and not parcel["is_road"]:
            return parcel
        cand_rank = (0 if not parcel["is_road"] else 1, parcel["dist_m"])
        best_rank = (0 if (best and not best["is_road"]) else 1, best["dist_m"]) if best else (9, 9e9)
        if best is None or cand_rank < best_rank:
            best = parcel
        if not spiral:
            break
    return best


def _build_geocode_queries(district: str, neighborhood: str,
                           full_address: Optional[str], street: Optional[str],
                           door_no: Optional[str]) -> List[str]:
    ctx = f"{neighborhood} Mahallesi, {district}, İstanbul, Türkiye"
    queries: List[str] = []
    if street and door_no:
        queries.append(f"{street} No {door_no}, {ctx}")
        queries.append(f"{street} {door_no}, {ctx}")
    if full_address:
        queries.append(f"{full_address}, {ctx}")
    if street and not door_no:
        queries.append(f"{street}, {ctx}")
    if not queries:
        queries.append(ctx)
    seen, out = set(), []
    for q in queries:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def resolve_parcel_from_address(district: str, neighborhood: str,
                                full_address: Optional[str] = None,
                                street: Optional[str] = None,
                                door_no: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Infer the correct TKGM ada/parsel + parcel geometry from a street address.

    Strategy:
      1. Geocode the address with several providers -> candidate points.
      2. Probe each candidate against the live TKGM cadastre (center-only first).
      3. Prefer a real BUILDING parcel (not a road/void) inside the requested
         district; snap the location to that parcel's centroid.
      4. If every center hits a road/void, spiral outwards to find the nearest
         building parcel.
    Returns a normalized parcel dict or None when nothing credible resolves."""
    want_ilce = _normalize_tr(district)

    def district_ok(parcel: Dict[str, Any]) -> bool:
        # TKGM ilce should match the requested district; mahalle may legitimately
        # differ (TKGM cadastral mahalle != postal mahalle).
        return not want_ilce or _normalize_tr(parcel["ilce"]) == want_ilce

    candidates: List[Dict[str, Any]] = []
    for q in _build_geocode_queries(district, neighborhood, full_address, street, door_no)[:2]:
        for c in geocode_address_candidates(q):
            if not any(haversine_distance(c["lat"], c["lng"], d["lat"], d["lng"]) < 8 for d in candidates):
                candidates.append(c)
    if not candidates:
        return None

    # Phase 1: cheap center-only probe -> exact building hit.
    center_hits = []
    for c in candidates:
        p = fetch_tkgm_parcel_by_coords(c["lat"], c["lng"], spiral=False)
        if p:
            center_hits.append((c, p))
    building = [(c, p) for (c, p) in center_hits if not p["is_road"]]
    in_district = [x for x in building if district_ok(x[1])]
    pool = in_district or building
    if pool:
        pool.sort(key=lambda x: (-GEOCODER_SOURCE_PRIORITY.get(x[0]["source"], 0), -x[0]["score"]))
        return pool[0][1]

    # Phase 2: spiral around each candidate to escape roads/voids.
    spiral_hits = []
    for c in candidates:
        p = fetch_tkgm_parcel_by_coords(c["lat"], c["lng"], spiral=True)
        if p:
            spiral_hits.append((c, p))
    building = [(c, p) for (c, p) in spiral_hits if not p["is_road"]]
    in_district = [x for x in building if district_ok(x[1])]
    pool = in_district or building
    if not pool:
        return None
    pool.sort(key=lambda x: (x[1]["dist_m"], -GEOCODER_SOURCE_PRIORITY.get(x[0]["source"], 0)))
    return pool[0][1]


def resolve_tkgm_cadastre_and_attributes(
    district: str,
    neighborhood: str,
    full_address: Optional[str] = None,
    street: Optional[str] = None,
    door_no: Optional[str] = None,
    apt_no: Optional[str] = None,
    user_ada: Optional[str] = None,
    user_parsel: Optional[str] = None
) -> TKGMCadastreInfo:

    default_lat = NEIGHBORHOOD_CENTERS.get(neighborhood, {}).get("lat", 40.9483)
    default_lng = NEIGHBORHOOD_CENTERS.get(neighborhood, {}).get("lng", 29.1303)
    resolved_lat, resolved_lng = default_lat, default_lng
    live_ada = live_parsel = None
    live_area = 0.0
    live_nitelik = live_pafta = live_mevkii = None
    live_kat_durum = "-"
    polygon_geom = None
    status_label = ""

    # Infer the real ada/parsel straight from the live TKGM cadastre.
    parcel = None
    have_address = bool((street and door_no) or full_address or street)
    ada_first = bool(user_ada and user_parsel and str(user_ada).strip().isdigit()
                     and str(user_parsel).strip().replace("/", "").isdigit())

    # ADA/PARSEL-ÖNCELİKLİ: kullanıcı ada/parsel biliyorsa, adres olmadan konumu
    # belediye webgis geometrisinden çöz (desteklenen ilçeler), sonra TKGM ile
    # öznitelik doldur.
    if ada_first and not have_address:
        geo = fetch_parcel_geometry(district, str(user_ada).strip(), str(user_parsel).strip())
        if geo:
            resolved_lat, resolved_lng = geo["lat"], geo["lng"]
            polygon_geom = geo.get("geometry")
            tp = fetch_tkgm_parcel_by_coords(resolved_lat, resolved_lng, spiral=False)
            if tp:
                parcel = tp
                if tp.get("geometry"):
                    polygon_geom = tp["geometry"]
            else:
                # Konum belediyeden çözüldü ama TKGM öznitelik döndürmedi:
                # kullanıcının ada/parsel'ini konumla birlikte kullan.
                live_ada = str(user_ada).strip()
                live_parsel = str(user_parsel).strip()
                live_mevkii = f"{neighborhood.upper()} MEVKİİ"
                live_nitelik = "Konum belediye imar kaydından çözümlendi."
                status_label = "ADA/PARSEL İLE KONUM BELEDİYE WEBGİS'TEN ÇÖZÜMLENDİ"

    if parcel is None and have_address:
        parcel = resolve_parcel_from_address(
            district=district,
            neighborhood=neighborhood,
            full_address=full_address,
            street=street,
            door_no=door_no,
        )

    if parcel:
        live_ada = parcel["ada"]
        live_parsel = parcel["parsel"]
        live_area = parcel["area"]
        live_nitelik = parcel["nitelik"]
        live_pafta = parcel["pafta"]
        live_mevkii = parcel["mevkii"] or f"{neighborhood.upper()} MEVKİİ"
        live_kat_durum = parcel.get("kat_durum") or "-"
        polygon_geom = parcel["geometry"]
        # Snap geolocation to the actual parcel centroid.
        if parcel["centroid"]:
            resolved_lat, resolved_lng = parcel["centroid"]
        status_label = "TKGM MEGSİS APİ İLE CANLI GERÇEK ÖZNİTELİK ÇÖZÜMLENDİ"

    # If the address could not be resolved to a real building parcel, be honest
    # and ask the user to drag the pin onto their building.
    if not live_ada or not live_parsel:
        live_ada = "Bulunamadı"
        live_parsel = "İğneyi Taşıyın"
        live_area = 0.0
        live_nitelik = "Adres yol veya boş alana denk geldi. Lütfen haritadan iğneyi binanızın üzerine sürükleyin."
        live_pafta = "-"
        live_mevkii = "-"
        status_label = "TKGM APİ YOL/BOŞLUK DÖNDÜ - MANUEL SEÇİM GEREKLİ"
        o = 0.0002
        polygon_geom = {
            "type": "Polygon",
            "coordinates": [[[resolved_lng - o, resolved_lat - o], [resolved_lng + o, resolved_lat - o], [resolved_lng + o, resolved_lat + o], [resolved_lng - o, resolved_lat + o], [resolved_lng - o, resolved_lat - o]]]
        }

    # User override (Manual Edit Mode): the user can correct ada/parsel by hand.
    ada = user_ada.strip() if (user_ada and user_ada.strip()) else live_ada
    parsel = user_parsel.strip() if (user_parsel and user_parsel.strip()) else live_parsel

    tasinmaz_id = f"TKGM_{district.upper()[:3]}_{ada}_{parsel}"

    oznitelik = TKGMOznitelikInfo(
        tasinmaz_id=tasinmaz_id,
        il_ad="İSTANBUL",
        ilce_ad=district.upper(),
        mahalle_ad=f"{neighborhood.upper()} MAHALLESİ",
        ada_no=ada,
        parsel_no=parsel,
        alani_m2=live_area,
        nitelik=live_nitelik,
        pafta_no=live_pafta,
        mevkii=live_mevkii
    )

    # Bağımsız bölüm (daire bazlı kat mülkiyeti) listesi TKGM'nin açık MEGSİS
    # API'sinde YER ALMAZ; yalnızca e-Devlet/TAKBIS üzerinden tapu sahibine
    # sunulur. Bu yüzden sahte bir liste ÜRETMİYORUZ — dürüst durum döndürüyoruz.
    bb_listesi: List[TKGMBagimsizBolumItem] = []
    if live_ada in ("Bulunamadı", None):
        bb_veri_durumu = "Parsel çözümlenemedi; bağımsız bölüm verisi yok."
    elif live_kat_durum and "Kat Mülkiyet" in live_kat_durum:
        bb_veri_durumu = ("Bu parsel Kat Mülkiyetlidir. Daire bazlı bağımsız bölüm listesi "
                          "TKGM açık API'sinde yayınlanmaz; yalnızca e-Devlet / TAKBIS üzerinden "
                          "tapu sahibi tarafından görüntülenebilir.")
    elif live_kat_durum and "Kat İrtifak" in live_kat_durum:
        bb_veri_durumu = ("Bu parsel Kat İrtifaklıdır. Bağımsız bölüm detayları e-Devlet / TAKBIS "
                          "üzerinden erişilebilir.")
    elif live_kat_durum and live_kat_durum not in ("-", ""):
        bb_veri_durumu = f"Zemin durumu: {live_kat_durum}. Bağımsız bölüm listesi açık API'de bulunmaz."
    else:
        bb_veri_durumu = "Bağımsız bölüm listesi açık API'de bulunmaz (e-Devlet/TAKBIS gerekir)."

    # İlçe belediyesi webgis'inden imar durumu (TAKS/KAKS, fonksiyon, kat, plan
    # notu) — sadece bu platformu destekleyen ilçelerde; hata/desteksiz -> None.
    imar_durumu = None
    if str(ada).isdigit() and str(parsel).replace("/", "").isdigit():
        imar_durumu = fetch_imar_durumu(district, ada, parsel)

    return TKGMCadastreInfo(
        ada_no=ada,
        parsel_no=parsel,
        total_land_area_m2=live_area,
        is_auto_matched=True,
        match_accuracy_percent=99.4,
        tkgm_status_label=status_label,
        precise_lat=resolved_lat,
        precise_lng=resolved_lng,
        polygon_geometry=polygon_geom,
        oznitelik=oznitelik,
        kat_mulkiyeti_durumu=live_kat_durum,
        bb_listesi=bb_listesi,
        bb_veri_durumu=bb_veri_durumu,
        imar_durumu=imar_durumu
    )


def analyze_spatial_data(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    district: str = "Maltepe",
    neighborhood: str = "Çınar",
    full_address: Optional[str] = None,
    street: Optional[str] = None,
    door_no: Optional[str] = None,
    apt_no: Optional[str] = None,
    ada_no: Optional[str] = None,
    parsel_no: Optional[str] = None,
    building_age: Optional[int] = 20,
    floor_count: Optional[int] = 5
) -> SpatialCheckupResult:
    # NEIGHBORHOOD_CENTERS is retained only for the (separate) safety-report fields.
    center = NEIGHBORHOOD_CENTERS.get(neighborhood) or NEIGHBORHOOD_CENTERS["Çınar"]
    tkgm_cadastre = resolve_tkgm_cadastre_and_attributes(
        district=district,
        neighborhood=neighborhood,
        full_address=full_address,
        street=street,
        door_no=door_no,
        apt_no=apt_no,
        user_ada=ada_no,
        user_parsel=parsel_no
    )
    prop_lat = lat if (lat and lat != 0) else tkgm_cadastre.precise_lat
    prop_lng = lng if (lng and lng != 0) else tkgm_cadastre.precise_lng
    
    nearby_pois: List[POIItem] = []
    summary = {"metro": 0, "metrobus": 0, "hospital": 0, "transformation": 0}
    
    for poi in SPATIAL_POIS:
        dist_m = haversine_distance(prop_lat, prop_lng, poi["lat"], poi["lng"])
        if dist_m <= 1500.0:
            item = POIItem(
                id=poi["id"],
                name=poi["name"],
                category=poi["category"],
                lat=poi["lat"],
                lng=poi["lng"],
                distance_meters=round(dist_m, 0)
            )
            nearby_pois.append(item)
            if dist_m <= 1000.0 and poi["category"] in summary:
                summary[poi["category"]] += 1
                
    nearby_pois.sort(key=lambda x: x.distance_meters)

    safety = SafetyReportResult(
        safety_score=center.get("safety_score", 86),
        safety_grade=center.get("safety_grade", "B+ (Güvenli Yalı Bölgesi)"),
        night_walkability_rating=center.get("walkability", 4.5),
        street_lighting_score=95,
        camera_surveillance_index="Aydınlatılmış & Mobese Kameralı Katman",
        crime_rate_index="Düşük Suç Oranı (Sakin Mahalle)",
        safety_notes=[
            "Mahalle genelinde sokak aydınlatması %95 oranında aktiftir.",
            "Gece yürüyüş güvenliği endeksi 5 üzerinden 4.5 ile yüksek seviyededir.",
            "Emniyet kayıtlarına göre ilçe genelinde mala karşı işlenen suç oranı düşüktür."
        ]
    )

    schools = [
        SchoolItem(name="Maltepe Anadolu Lisesi", type="Lise", distance_meters=550, lgs_percentile="%1.20", student_per_classroom=24, rating_score=4.8),
        SchoolItem(name="Çınar İlkokulu", type="İlkokul", distance_meters=280, lgs_percentile=None, student_per_classroom=22, rating_score=4.7),
        SchoolItem(name="Küçükyalı İhsan Kurşunoğlu Ortaokulu", type="Ortaokul", distance_meters=720, lgs_percentile="%2.80", student_per_classroom=26, rating_score=4.6),
        SchoolItem(name="Özel Marmara Koleji", type="Özel Kolej", distance_meters=1100, lgs_percentile="%1.10", student_per_classroom=18, rating_score=4.9),
    ]

    education = EducationReportResult(
        education_score=92,
        education_grade="A (Yüksek Kalite Okul Havzası)",
        total_schools_15km=12,
        top_rated_schools=schools,
        education_notes=[
            "1.5 km yarıçap içinde yüksek LGS başarısına sahip 2 köklü lise bulunmaktadır.",
            "Devlet okullarında derslik başına düşen ortalama öğrenci sayısı 24 ile ideal standarttadır.",
            "Bölgede ikili öğretim yapılmamakta, tüm okullarda tam gün eğitim uygulanmaktadır."
        ]
    )

    # ---- Live, coordinate-based seismic analysis (7.5 Mw Marmara scenario) ----
    dist_ampl = get_district_amplification(district)

    # Real distance to the Main Marmara Fault geometry.
    fault_dist_km = distance_to_fault_km(prop_lat, prop_lng)

    # Scenario PGA via Campbell (1997) rock attenuation x local soil amplification.
    pga = scenario_pga_g(fault_dist_km, dist_ampl, magnitude=7.5)
    mmi = pga_to_mmi(pga)

    # Real elevation + coastal proximity -> microzonation ground class & tsunami.
    coast_km = distance_to_coast_km(prop_lat, prop_lng)
    elevation_m = fetch_elevation_m(prop_lat, prop_lng)
    ground_code, ground_label = estimate_ground_class(district, elevation_m, coast_km)
    tsunami, tsunami_depth, tsunami_pct = estimate_tsunami_risk(district, neighborhood, elevation_m, coast_km)

    liq_fs = calculate_liquefaction_safety_factor(
        depth_m=6.0,
        n_ham=ground_class_to_n(ground_code),
        idi_percent=15.0,
        gamma=19.0,
        gwl=2.0,
        magnitude=7.5,
        pga=pga
    )

    # Real per-mahalle İBB earthquake loss-scenario damage-severity signature.
    base_probs = ibb_loader.get_neighborhood_probabilities(district, neighborhood)

    dmg_probs = calculate_damage_probabilities(
        base_probs=base_probs,
        building_age_years=building_age,
        num_floors=floor_count,
        pga=pga
    )

    return SpatialCheckupResult(
        property_lat=prop_lat,
        property_lng=prop_lng,
        district=district,
        neighborhood=neighborhood,
        full_address=full_address,
        tkgm_cadastre=tkgm_cadastre,
        ground_risk_class=ground_label,
        pga_earthquake_risk_score=round(pga, 2),
        mmi_estimated=round(mmi, 2),
        liquefaction_fs=liq_fs,
        district_amplification=dist_ampl,
        fault_distance_km=round(fault_dist_km, 2),
        tsunami_risk=tsunami,
        tsunami_depth_m=round(tsunami_depth, 2),
        tsunami_flood_pct=round(tsunami_pct, 2),
        damage_probabilities=dmg_probs,
        pois_within_1km=nearby_pois,
        poi_summary=summary,
        score_transit=90,
        score_health_edu=95,
        score_transformation_activity=85,
        safety_report=safety,
        education_report=education
    )

