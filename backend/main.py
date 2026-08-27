import io
import os
import re
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.input_parser import parse_ad_text, ParsedAdInput
from services.valuation_engine import calculate_valuation, ValuationResult, DISTRICT_BASE_PRICES
from services.urban_transformation import simulate_urban_transformation, UrbanTransformationResult
from services.financial_engine import calculate_financials, FinancialYieldResult
from services.spatial_service import analyze_spatial_data, SpatialCheckupResult, resolve_tkgm_cadastre_and_attributes
from services.pdf_report import generate_checkup_pdf
from services.tcmb_service import get_tcmb_kfe_summary
from services.observation_log import kaydet as _gozlem_kaydet
from services import address_service as _adres

app = FastAPI(
    title="rayic.org API",
    description="Real Estate Valuation, Urban Transformation & TKGM Cadastre Engine",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ValuationRequest(BaseModel):
    price: float
    net_m2: float
    gross_m2: Optional[float] = None
    building_age: Optional[int] = 20
    floor_count: Optional[int] = 5
    floor_category: str = "ara_kat"
    floor_name: Optional[str] = "3. Kat"
    room_count: Optional[str] = "3+1"
    total_land_m2: Optional[float] = 2400
    land_share_num: Optional[float] = None
    land_share_den: Optional[float] = None
    district: str = "Maltepe"
    neighborhood: str = "Çınar"
    full_address: Optional[str] = None
    street: Optional[str] = None
    door_no: Optional[str] = None
    apt_no: Optional[str] = None
    ada_no: Optional[str] = None
    parsel_no: Optional[str] = None
    contractor_share_ratio: float = 0.50
    lat: Optional[float] = None
    lng: Optional[float] = None

class CadastreLookupRequest(BaseModel):
    district: str
    neighborhood: str
    street: Optional[str] = None
    door_no: Optional[str] = None
    apt_no: Optional[str] = None
    full_address: Optional[str] = None
    user_ada: Optional[str] = None
    user_parsel: Optional[str] = None

class FullCheckupResponse(BaseModel):
    ad_input: Dict[str, Any]
    valuation: ValuationResult
    urban_transformation: UrbanTransformationResult
    financials: FinancialYieldResult
    spatial: SpatialCheckupResult
    tcmb_kfe: Dict[str, Any]

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "rayic.org Real Estate Valuation & TKGM API",
        "version": "1.2.0"
    }

# ---------------------------------------------------------------------------
# RESMİ ADRES SEÇİMİ (İBB e-Plan). Kullanıcı adres YAZMAZ, listeden SEÇER:
# ilçe -> mahalle -> sokak -> kapı. Kapı seçilince binanın kendi koordinatı ve
# oradan ada/parsel kesin olarak gelir; adres ayrıştırma tahmini ortadan kalkar.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# MAHALLE & İLÇE REHBERİ — paywall'suz, SEO için açık uçlar.
# Yalnızca gerçek kaynaklardan üretilir (İBB deprem senaryosu, İBB nüfus,
# Ağustos 2026 piyasa raporu, OSM raylı/kıyı, MeTHuVA tsunami).
# ---------------------------------------------------------------------------
def _rehber():
    global _REHBER
    try:
        return _REHBER
    except NameError:
        pass
    import json as _json
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "data", "mahalle_rehberi.json"), encoding="utf-8") as f:
            _REHBER = _json.load(f)
    except Exception:
        _REHBER = {"meta": {}, "ilceler": {}}
    return _REHBER


def _nrm_reh(s):
    s = (s or "").strip().lower()
    for a, b in (("ı", "i"), ("İ", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"),
                 ("ö", "o"), ("ç", "c"), ("â", "a"), ("-", " ")):
        s = s.replace(a, b)
    return " ".join(s.split())


@app.get("/api/v1/rehber/ilceler")
def rehber_ilceler():
    """Tüm ilçeler + özet (mahalle sayısı, medyan fiyat, demografi)."""
    r = _rehber()
    out = []
    for ad, v in r["ilceler"].items():
        ms = list(v["mahalleler"].values())
        sat = sorted(m["satilik_tlm2"] for m in ms if m.get("satilik_tlm2"))
        kir = sorted(m["kiralik_tlm2"] for m in ms if m.get("kiralik_tlm2"))
        out.append({
            "ad": ad, "slug": _nrm_reh(ad).replace(" ", "-"),
            "mahalle_sayisi": len(ms),
            "medyan_satilik_tlm2": sat[len(sat) // 2] if sat else None,
            "medyan_kiralik_tlm2": kir[len(kir) // 2] if kir else None,
            "demografi": v.get("demografi"),
        })
    out.sort(key=lambda x: x["ad"])
    return {"meta": r.get("meta", {}), "ilceler": out}


@app.get("/api/v1/rehber/ilce/{slug}")
def rehber_ilce(slug: str):
    """Bir ilçenin tüm mahalleleri ve göstergeleri."""
    r = _rehber()
    for ad, v in r["ilceler"].items():
        if _nrm_reh(ad).replace(" ", "-") == _nrm_reh(slug).replace(" ", "-"):
            ms = sorted(v["mahalleler"].values(), key=lambda m: m["ad"])
            for m in ms:
                m["slug"] = _nrm_reh(m["ad"]).replace(" ", "-")
            return {"ad": ad, "demografi": v.get("demografi"), "mahalleler": ms}
    return {"bulundu": False, "mesaj": "İlçe bulunamadı."}


@app.get("/api/v1/rehber/mahalle/{ilce_slug}/{mahalle_slug}")
def rehber_mahalle(ilce_slug: str, mahalle_slug: str):
    """Tek mahallenin tam profili (SEO sayfası bunu kullanır)."""
    r = _rehber()
    for ad, v in r["ilceler"].items():
        if _nrm_reh(ad).replace(" ", "-") != _nrm_reh(ilce_slug).replace(" ", "-"):
            continue
        for mad, m in v["mahalleler"].items():
            if _nrm_reh(mad).replace(" ", "-") == _nrm_reh(mahalle_slug).replace(" ", "-"):
                return {"ilce": ad, "ilce_demografi": v.get("demografi"), **m}
    return {"bulundu": False, "mesaj": "Mahalle bulunamadı."}


@app.get("/api/v1/adres/ilceler")
def adres_ilceler():
    return {"ilceler": _adres.ilceler()}


@app.get("/api/v1/adres/mahalleler")
def adres_mahalleler(ilce_id: int):
    return {"mahalleler": _adres.mahalleler(ilce_id)}


@app.get("/api/v1/adres/sokaklar")
def adres_sokaklar(mahalle_id: int):
    return {"sokaklar": _adres.sokaklar(mahalle_id)}


@app.get("/api/v1/adres/kapilar")
def adres_kapilar(mahalle_id: int, sokak_id: int):
    return {"kapilar": _adres.kapilar(mahalle_id, sokak_id)}


@app.get("/api/v1/adres/coz")
def adres_coz(ilce_id: int, mahalle_id: int, sokak_id: int, kapi_id: int):
    """Seçilen kapı -> koordinat + ada/parsel (wizard bunu kullanır)."""
    r = _adres.adres_coz(ilce_id, mahalle_id, sokak_id, kapi_id)
    if not r:
        return {"bulundu": False,
                "mesaj": "Bu kapı için konum alınamadı. Ada/parsel ile devam edebilirsiniz."}
    return {"bulundu": True, **r}


@app.post("/api/v1/cadastre-lookup")
def lookup_cadastre(req: CadastreLookupRequest):
    tkgm_info = resolve_tkgm_cadastre_and_attributes(
        district=req.district,
        neighborhood=req.neighborhood,
        full_address=req.full_address,
        street=req.street,
        door_no=req.door_no,
        apt_no=req.apt_no,
        user_ada=req.user_ada,
        user_parsel=req.user_parsel
    )
    return tkgm_info

@app.post("/api/v1/valuate")
def valuate_property(req: ValuationRequest):
    val_res = calculate_valuation(
        price_advertised=req.price,
        net_m2=req.net_m2,
        building_age=req.building_age,
        floor_category=req.floor_category,
        district=req.district,
        neighborhood=req.neighborhood,
        # Mahalle içi konum çarpanı için koordinat (adres dropdown'ından gelir)
        lat=req.lat,
        lng=req.lng,
    )

    urb_res = simulate_urban_transformation(
        advertised_price=req.price,
        current_net_m2=req.net_m2,
        total_land_m2=req.total_land_m2,
        land_num=req.land_share_num,
        land_den=req.land_share_den,
        contractor_share_ratio=req.contractor_share_ratio,
        district=req.district,
        neighborhood=req.neighborhood
    )

    fin_res = calculate_financials(
        advertised_price=req.price,
        net_m2=req.net_m2,
        district=req.district,
        building_age=req.building_age or 10,
        neighborhood=req.neighborhood,
        lat=req.lat,
        lng=req.lng,
    )

    spatial_res = analyze_spatial_data(
        lat=req.lat,
        lng=req.lng,
        district=req.district,
        neighborhood=req.neighborhood,
        full_address=req.full_address,
        street=req.street,
        door_no=req.door_no,
        apt_no=req.apt_no,
        ada_no=req.ada_no,
        parsel_no=req.parsel_no,
        building_age=req.building_age,
        floor_count=req.floor_count
    )

    # Her ekspertiz talebi aynı zamanda bir GEOCODED FİYAT GÖZLEMİdir: adresi
    # TKGM ile parsel koordinatına çözdük, ilan fiyatı ve m² elimizde. Mahalle
    # İÇİ konum çarpanı ancak bu gözlemler birikince GERÇEK veriyle kestirilebilir
    # (hazır veri setlerinde koordinat yok, portallar otomatik erişime kapalı).
    try:
        _gozlem_kaydet(
            lat=getattr(spatial_res, "property_lat", None),
            lng=getattr(spatial_res, "property_lng", None),
            district=req.district, neighborhood=req.neighborhood,
            price=req.price, net_m2=req.net_m2,
            building_age=req.building_age, floor_category=req.floor_category,
            ada_no=getattr(getattr(spatial_res, "tkgm_cadastre", None), "ada_no", None),
            parsel_no=getattr(getattr(spatial_res, "tkgm_cadastre", None), "parsel_no", None),
        )
    except Exception:
        pass

    tcmb_data = get_tcmb_kfe_summary()

    return {
        "ad_input": req.dict(),
        "valuation": val_res,
        "urban_transformation": urb_res,
        "financials": fin_res,
        "spatial": spatial_res,
        "tcmb_kfe": tcmb_data
    }
