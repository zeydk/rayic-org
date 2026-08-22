"""İlçe belediyesi imar durumu sorgusu — çok platformlu + yerel önbellek (stok).

Belediyelerin webgis "İmar Durumu" uygulamaları ada/parsel ile sorgulanabiliyor.
Farklı ilçeler farklı platform kullanıyor; her platform için ayrı adaptör var:

  * netgis  (NETCAD/NETGIS)  -> imarsvc.aspx (svc_nonce + X-Service-Nonce)
              1) GET {base}                     -> svc_nonce çerezi
              2) imarsvc.aspx?type=adaparsel..  -> OBJECTID
              3) imar.aspx?parselid=OBJECTID    -> imar durumu belgesi (HTML)

Dış servisler yavaş / URL'leri değişebilir olduğundan, başarılı her sonuç
`data/imar_cache.json` içine STOKLANIR. Sonraki sorgular önce önbellekten
karşılanır — böylece hem hızlı hem de kaynak adres değişse/çökse bile dayanıklı.
"""
import os
import re
import json
import html as _html
import threading
from typing import Dict, Any, Optional

import requests

# ---------------------------------------------------------------------------
# İlçe (normalize) -> {platform, base}. Aynı NETGIS platformunu kullanan ve
# ada/parsel ile sorgulanabilen ilçeler (uçtan uca doğrulandı).
# ---------------------------------------------------------------------------
MUNICIPAL_WEBGIS: Dict[str, Dict[str, str]] = {
    "kadikoy":    {"platform": "netgis", "base": "https://webgis.kadikoy.bel.tr/imardurumu/"},
    "maltepe":    {"platform": "netgis", "base": "https://webgis.maltepe.bel.tr/imardurumu/"},
    "atasehir":   {"platform": "netgis", "base": "https://webgis.atasehir.bel.tr/imardurumu/"},
    "umraniye":   {"platform": "netgis", "base": "https://webgis.umraniye.bel.tr/imardurumu/"},
    "cekmekoy":   {"platform": "netgis", "base": "https://webgis.cekmekoy.bel.tr/imardurumu/"},
    "sancaktepe": {"platform": "netgis", "base": "https://webgis.sancaktepe.bel.tr/imardurumu/"},
    "tuzla":      {"platform": "netgis", "base": "https://webgis.tuzla.bel.tr/imardurumu/"},
    "sultangazi": {"platform": "netgis", "base": "https://webgis.sultangazi.bel.tr/imardurumu/"},
    "basaksehir": {"platform": "netgis", "base": "https://webgis.basaksehir.bel.tr/imardurumu/"},
    "silivri":    {"platform": "netgis", "base": "https://webgis.silivri.bel.tr/imardurumu/"},
    "gungoren":   {"platform": "netgis", "base": "https://keos.gungoren.bel.tr:3443/imardurumu/"},
    # İBB/ArcGIS "Kent Rehberi" platformu (AdaParsel + PlanBinaYok mekansal sorgu).
    "uskudar":    {"platform": "arcgis_kentrehberi",
                   "gis": "https://harita.uskudar.bel.tr/server/rest/services/KENTREHBERI",
                   "eharita": "https://cbs.uskudar.bel.tr/eharita/"},
}

# ArcGIS KULLANIM kodları için yedek eşleme (domain yoksa).
_KULLANIM_FALLBACK = {
    1: "Konut", 2: "Ticaret", 3: "Konut + Ticaret", 4: "Sanayi", 5: "Turizm",
    6: "Yeşil Alan", 7: "Donatı", 8: "Resmi Kurum", 9: "Eğitim", 10: "Sağlık",
}

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36")

_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "imar_cache.json")
_cache_lock = threading.Lock()


def _load_cache() -> Dict[str, Any]:
    try:
        with open(_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_IMAR_CACHE: Dict[str, Any] = _load_cache()


def _save_cache() -> None:
    try:
        tmp = _CACHE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_IMAR_CACHE, f, ensure_ascii=False)
        os.replace(tmp, _CACHE_PATH)
    except Exception:
        pass


def _norm(s: Optional[str]) -> str:
    s = (s or "").strip().lower()
    for a, b in (("ı", "i"), ("İ", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"),
                 ("ö", "o"), ("ç", "c"), ("â", "a")):
        s = s.replace(a, b)
    return s


def _cache_key(district: str, ada: str, parsel: str) -> str:
    return f"{_norm(district)}|{ada}|{parsel}"


def _strip_html(t: str) -> str:
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# Belge etiketi -> normalize anahtar. Belgedeki HER alanı `tum_alanlar` içinde
# ayrıca ham olarak da döndürüyoruz (algoritmalarda kullanmak için).
_LABEL_MAP = {
    "Plan Fonksiyon": "fonksiyon", "Fonksiyon": "fonksiyon",
    "Bina Yüksekliği": "bina_yuksekligi", "Kat Adedi": "kat_adedi",
    "İnşaat Nizamı": "insaat_nizami", "T.A.K.S.": "taks", "TAKS": "taks",
    "K.A.K.S.": "kaks", "KAKS": "kaks", "Emsal": "emsal",
    "Ön Bahçe": "on_bahce", "Yan Bahçe": "yan_bahce", "Arka Bahçe": "arka_bahce",
    "Bina Derinliği": "bina_derinligi", "Bina Genişliği": "bina_genisligi",
    "Pafta": "pafta", "Mer'i İmar Planı": "imar_plani",
    "İdari Mahalle": "idari_mahalle", "Kot Alınacak Nokta": "kot_noktasi",
    "Tasdik Tarihi": "tasdik_tarihi", "Kısıtlama": "kisitlama",
}


def _clean_val(raw: str) -> str:
    # Tooltip/span attribute leaks -> keep only real inner text.
    if "data-ref" in raw or "data-placement" in raw or "title=" in raw:
        inner = re.findall(r">([^<>]+)<", raw)
        if inner:
            raw = " ".join(inner)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", raw))
    t = re.sub(r"\s+", " ", t).strip()
    if t in ("EMPTYROW", "-", ".", ""):
        return ""
    return re.sub(r"\s*(Harita|Google Maps|TKGM\|Parsel Sorgu)\s*$", "", t).strip()


def _extract_imar(doc: str) -> Dict[str, Any]:
    """NETGIS imar durumu belgesinden TÜM alanları ayıklar.

    Döner: normalize anahtarlar (fonksiyon, taks, kaks, bina_yuksekligi, on_bahce,
    yan_bahce, arka_bahce, bina_derinligi, bina_genisligi, kat_adedi, insaat_nizami,
    pafta, parsel_alani, imar_plani ...) + `tum_alanlar` (ham etiket->değer) +
    `plan_notlari` (tam metin)."""
    out: Dict[str, Any] = {}
    tum: Dict[str, str] = {}

    pairs = re.findall(
        r'divTableCellLabel[^"]*"[^>]*>(.*?)</div>\s*'
        r'<div class="divTableCell divTableContent"[^>]*>(.*?)</div>',
        doc, re.DOTALL)
    for lbl_raw, val_raw in pairs:
        label = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", lbl_raw))).strip()
        val = _clean_val(val_raw)
        if not label or label in (".", "EMPTYROW"):
            continue
        if label.startswith("Parsel Alanı") and val:
            out["parsel_alani"] = val.split("(")[0].strip()
        if label in _LABEL_MAP and val:
            out.setdefault(_LABEL_MAP[label], val)
        if val:
            tum[label] = val

    # Plan notları (numaralı liste) — tam metin.
    txt = _strip_html(doc)
    mnot = re.search(r"Plan Notlar[ıi][^0-9]{0,40}(1\s*-\s*.+?)(?:Yazd[ıi]r|Bu belge|©|$)", txt)
    if mnot:
        notes = re.sub(r"\s+", " ", mnot.group(1)).strip()
        if len(notes) > 30:
            out["plan_notlari"] = notes[:1500]

    if tum:
        out["tum_alanlar"] = tum
    return out


# ---------------------------------------------------------------------------
# Platform adaptörleri
# ---------------------------------------------------------------------------
def _query_netgis(cfg: Dict[str, str], district: str, ada: str, parsel: str) -> Optional[Dict[str, Any]]:
    base = cfg["base"]
    s = requests.Session()
    s.headers.update({"User-Agent": _UA})
    s.get(base, timeout=8, verify=False)
    nonce = s.cookies.get("svc_nonce") or ""
    h = {"Referer": base, "X-Service-Nonce": nonce, "X-Requested-With": "XMLHttpRequest"}

    r = s.get(base + "service/imarsvc.aspx",
              params={"type": "adaparsel", "adaparsel": f"{ada}/{parsel}"},
              headers=h, timeout=8, verify=False)
    arr = r.json()
    if not isinstance(arr, list) or not arr:
        return None
    oid = arr[0].get("OBJECTID")
    tapu_mah = arr[0].get("TAPU_MAH_ADI", "")
    if not oid:
        return None

    doc = s.get(base + "imar.aspx", params={"parselid": oid},
                headers={"Referer": base, "X-Service-Nonce": nonce},
                timeout=15, verify=False).text
    fields = _extract_imar(doc)
    if not fields:
        return None

    return {
        "supported": True,
        "belediye": district.strip().title() + " Belediyesi",
        "ada_parsel": f"{ada}/{parsel}",
        "tapu_mahalle": tapu_mah,
        "kaynak_url": f"{base}imar.aspx?parselid={oid}",
        **fields,
    }


def fetch_parcel_geometry(district: str, ada: str, parsel: str) -> Optional[Dict[str, Any]]:
    """Belediye webgis'inden ada/parsel'e ait GEOMETRİ (poligon + merkez).
    Ada/parsel-öncelikli akışta konumu adres olmadan bulmak için. Desteklenen
    ilçe değilse / hata -> None."""
    cfg = MUNICIPAL_WEBGIS.get(_norm(district))
    if not cfg or not ada or not parsel:
        return None

    # ArcGIS Kent Rehberi: AdaParsel katmanından geometri (4326).
    if cfg["platform"] == "arcgis_kentrehberi":
        try:
            gis = cfg["gis"]
            j = _agq(gis + "/AdaParsel/MapServer/1/query",
                     {"where": "ADANO='%s' AND ADINUMARASI='%s'" % (ada, parsel),
                      "outFields": "MAHALLE", "returnGeometry": "true", "outSR": "4326"})
            feats = j.get("features", [])
            if not feats:
                return None
            ring = feats[0]["geometry"]["rings"][0]
            cx = sum(p[0] for p in ring) / len(ring)
            cy = sum(p[1] for p in ring) / len(ring)
            geom = {"type": "Polygon", "coordinates": [[[p[0], p[1]] for p in ring]]}
            return {"lat": cy, "lng": cx, "geometry": geom,
                    "tapu_mahalle": feats[0]["attributes"].get("MAHALLE", "")}
        except Exception:
            return None

    if cfg["platform"] != "netgis":
        return None
    base = cfg["base"]
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": _UA})
        s.get(base, timeout=8, verify=False)
        nonce = s.cookies.get("svc_nonce") or ""
        h = {"Referer": base, "X-Service-Nonce": nonce, "X-Requested-With": "XMLHttpRequest"}
        r = s.get(base + "service/imarsvc.aspx",
                  params={"type": "adaparsel", "adaparsel": f"{ada}/{parsel}"},
                  headers=h, timeout=8, verify=False)
        arr = r.json()
        if not isinstance(arr, list) or not arr:
            return None
        oid = arr[0].get("OBJECTID")
        tapu_mah = arr[0].get("TAPU_MAH_ADI", "")
        rp = s.get(base + "service/imarsvc.aspx",
                   params={"type": "parsel", "parselid": oid},
                   headers=h, timeout=8, verify=False)
        rec = rp.json()[0]
        geom = json.loads(rec["POLY"]) if rec.get("POLY") else None
        centroid = None
        if geom and geom.get("coordinates"):
            ring = geom["coordinates"][0] if geom["type"] == "Polygon" else geom["coordinates"][0][0]
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            centroid = (sum(ys) / len(ys), sum(xs) / len(xs))  # (lat, lng)
        return {"lat": centroid[0], "lng": centroid[1], "geometry": geom,
                "tapu_mahalle": tapu_mah} if centroid else None
    except Exception:
        return None


# ArcGIS coded-value domain cache (gis_base -> {field -> {code: label}}).
_ARCGIS_DOMAINS: Dict[str, Dict[str, Dict[Any, str]]] = {}


def _arcgis_domains(gis: str) -> Dict[str, Dict[Any, str]]:
    if gis in _ARCGIS_DOMAINS:
        return _ARCGIS_DOMAINS[gis]
    out: Dict[str, Dict[Any, str]] = {}
    try:
        f = requests.get(gis + "/PlanBinaYok/MapServer/221?f=json", timeout=10, verify=False).json()
        for fl in f.get("fields", []):
            dom = fl.get("domain")
            if dom and dom.get("codedValues"):
                out[fl["name"]] = {c["code"]: c["name"] for c in dom["codedValues"]}
    except Exception:
        pass
    _ARCGIS_DOMAINS[gis] = out
    return out


def _agq(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(params)
    params["f"] = "json"
    return requests.get(url, params=params, timeout=12, verify=False).json()


def _query_arcgis_kentrehberi(cfg: Dict[str, str], district: str, ada: str, parsel: str) -> Optional[Dict[str, Any]]:
    """İBB/ArcGIS 'Kent Rehberi' platformu: AdaParsel katmanından parsel geometrisi,
    PlanBinaYok/221 (PLAN ADASI) katmanından mekansal kesişimle YAPISAL imar verisi
    (TAKS/KAKS, fonksiyon, yapı düzeni, bahçe mesafeleri, kat, yükseklik...)."""
    gis = cfg["gis"]
    where = "ADANO='%s' AND ADINUMARASI='%s'" % (ada, parsel)
    j = _agq(gis + "/AdaParsel/MapServer/1/query",
             {"where": where, "outFields": "ID,PAFTANO,ALANI,MAHALLE",
              "returnGeometry": "true", "outSR": "4326"})
    feats = j.get("features", [])
    if not feats:
        return None
    a = feats[0]["attributes"]
    ring = feats[0].get("geometry", {}).get("rings", [[]])[0]
    if not ring:
        return None
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)

    pt = json.dumps({"x": cx, "y": cy, "spatialReference": {"wkid": 4326}})
    pj = _agq(gis + "/PlanBinaYok/MapServer/221/query",
              {"geometry": pt, "geometryType": "esriGeometryPoint", "inSR": "4326",
               "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "false"})
    pf = pj.get("features", [])
    plan = pf[0]["attributes"] if pf else {}
    return _build_arcgis_record(cfg, district, ada, parsel, a, plan, _arcgis_domains(gis), cy, cx)


def _build_arcgis_record(cfg, district, ada, parsel, a, plan, dom, lat, lng):
    """ArcGIS parsel + plan öznitelikelrinden normalize imar kaydı üretir."""
    kod = plan.get("KULLANIM")
    fonksiyon = (dom.get("KULLANIM", {}).get(kod) or _KULLANIM_FALLBACK.get(kod))
    nizam = dom.get("YAPIDUZENI", {}).get(plan.get("YAPIDUZENI"))

    def val(v):
        return v if v not in (None, "", " ", 0) else None

    out: Dict[str, Any] = {
        "supported": True,
        "belediye": district.strip().title() + " Belediyesi",
        "ada_parsel": "%s/%s" % (ada, parsel),
        "tapu_mahalle": a.get("MAHALLE", ""),
        "pafta": a.get("PAFTANO"),
        "parsel_alani": ("%.2f m²" % a["ALANI"]) if a.get("ALANI") else None,
        "kaynak_url": "%s#/imardurum?id=%s" % (cfg.get("eharita", ""), a.get("ID", "")),
        "_lat": lat, "_lng": lng,
    }
    if fonksiyon:
        out["fonksiyon"] = fonksiyon
    if nizam:
        out["insaat_nizami"] = nizam
    for key, col in (("taks", "TAKS"), ("kaks", "KAKS"), ("kat_adedi", "KATADEDI"),
                     ("on_bahce", "ONBAHCEMESAFESI"), ("yan_bahce", "YANBAHCEMESAFESI"),
                     ("arka_bahce", "ARKABAHCEMESAFESI"), ("bina_yuksekligi", "MAKSBINAYUKSEKLIK"),
                     ("bina_derinligi", "MAKSDERINLIK"), ("min_cephe", "MINCEPHE")):
        v = val(plan.get(col))
        if v is not None:
            out[key] = v
    tum = {}
    for k, v in plan.items():
        if val(v) is not None and not k.startswith(("SHAPE", "OBJECTID", "GLOBALID")):
            tum[k] = dom.get(k, {}).get(v, v)
    if tum:
        out["tum_alanlar"] = tum
    return out if (fonksiyon or "taks" in out or "kat_adedi" in out) else None


_ADAPTERS = {
    "netgis": _query_netgis,
    "arcgis_kentrehberi": _query_arcgis_kentrehberi,
}


def _query_live(district: str, ada: str, parsel: str) -> Optional[Dict[str, Any]]:
    cfg = MUNICIPAL_WEBGIS.get(_norm(district))
    if not cfg:
        return None
    adapter = _ADAPTERS.get(cfg["platform"])
    if not adapter:
        return None
    try:
        return adapter(cfg, district, ada, parsel)
    except Exception:
        return None


def _pip(x: float, y: float, ring) -> bool:
    """Ray-casting point-in-polygon."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def _agq_all(url: str, out_fields: str, want_geom: bool):
    """Sayfalı olarak bir ArcGIS katmanının TÜM kayıtlarını çeker."""
    feats = []
    offset = 0
    while True:
        p = {"where": "1=1", "outFields": out_fields, "returnGeometry": str(want_geom).lower(),
             "outSR": "4326", "resultOffset": offset, "resultRecordCount": 2000,
             "orderByFields": "OBJECTID", "f": "json"}
        j = requests.get(url, params=p, timeout=25, verify=False).json()
        fs = j.get("features", [])
        feats.extend(fs)
        if len(fs) < 2000 or not j.get("exceededTransferLimit", len(fs) == 2000):
            if len(fs) < 2000:
                break
        offset += 2000
        if offset > 200000:
            break
    return feats


def bulk_fetch_arcgis(district: str, progress=None) -> int:
    """ArcGIS 'Kent Rehberi' ilçesi için TÜM parsellerin imar verisini toplu çeker:
    tüm plan adaları + tüm parseller alınır, yerel point-in-polygon ile eşleştirilir
    ve stoka yazılır. Per-parsel sunucu sorgusu YOK -> çok hızlı. Stoklanan sayı."""
    cfg = MUNICIPAL_WEBGIS.get(_norm(district))
    if not cfg or cfg["platform"] != "arcgis_kentrehberi":
        return 0
    gis = cfg["gis"]
    dom = _arcgis_domains(gis)

    # 1) tüm plan adaları (imar + geometri)
    plan_feats = _agq_all(gis + "/PlanBinaYok/MapServer/221/query",
                          "KULLANIM,ALTKULLANIM,YAPIDUZENI,TAKS,KAKS,ONBAHCEMESAFESI,"
                          "YANBAHCEMESAFESI,ARKABAHCEMESAFESI,KATADEDI,MAKSBINAYUKSEKLIK,"
                          "MAKSDERINLIK,MINCEPHE", True)
    plans = []
    for pf in plan_feats:
        rings = pf.get("geometry", {}).get("rings")
        if not rings:
            continue
        ring = rings[0]
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        plans.append((min(xs), min(ys), max(xs), max(ys), ring, pf["attributes"]))
    if progress:
        progress("plan adaları: %d" % len(plans))

    # 2) tüm parseller (ada/parsel + geometri)
    par_feats = _agq_all(gis + "/AdaParsel/MapServer/1/query",
                         "ID,ADANO,ADINUMARASI,MAHALLE,PAFTANO,ALANI", True)
    if progress:
        progress("parseller: %d" % len(par_feats))

    stocked = 0
    for pf in par_feats:
        a = pf["attributes"]
        ada = a.get("ADANO"); parsel = a.get("ADINUMARASI")
        rings = pf.get("geometry", {}).get("rings")
        if not ada or not parsel or not rings:
            continue
        ring = rings[0]
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        # bbox ile filtrele, sonra PIP
        plan = None
        for mnx, mny, mxx, mxy, pring, pattr in plans:
            if mnx <= cx <= mxx and mny <= cy <= mxy and _pip(cx, cy, pring):
                plan = pattr
                break
        if plan is None:
            continue
        rec = _build_arcgis_record(cfg, district, str(ada), str(parsel), a, plan, dom, cy, cx)
        if rec:
            key = _cache_key(district, str(ada), str(parsel))
            _IMAR_CACHE[key] = rec
            stocked += 1
    _save_cache()
    return stocked


def fetch_imar_durumu(district: str, ada: str, parsel: str,
                      use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """İlçe belediyesi imar durumu. Önce yerel stoktan (önbellek) bakar; yoksa
    canlı sorgular ve başarılı sonucu stoklar. Desteklenmeyen ilçe / hata -> None."""
    if not ada or not parsel:
        return None
    if not str(ada).isdigit() or not str(parsel).replace("/", "").isdigit():
        return None

    key = _cache_key(district, ada, parsel)
    if use_cache and key in _IMAR_CACHE:
        rec = _IMAR_CACHE[key]
        return {**rec, "cached": True} if rec else None

    result = _query_live(district, ada, parsel)
    if result is not None:
        with _cache_lock:
            _IMAR_CACHE[key] = result
            _save_cache()
    return result
