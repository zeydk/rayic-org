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
import io
import json
import time
import fcntl
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
    # Pendik de NETGIS: giriş noktası Kent Rehberi (_keos) olduğu için gizli
    # kalmıştı; imar servisi /imardurumu/ altında. `search_proxy` ise KEOS'un
    # OGC-Features arama ucu — toplu parsel ENUMERASYONU için kullanılır.
    "pendik":     {"platform": "netgis",
                   "base": "https://keos.pendik.bel.tr/imardurumu/",
                   "search_proxy": "https://cbsproxy.pendik.bel.tr",
                   "kentrehberi": "https://keos.pendik.bel.tr/_keos/"},
    # GiSoft GIS platformu (anonim JWT + entity/report + PDF imar belgesi).
    "beylikduzu": {"platform": "gisoft",
                   "base": "https://cbs.beylikduzu.istanbul/GiSoftGis",
                   "app": "GISOFT_GIS_WEB_CLIENT",
                   "eharita": "https://cbs.beylikduzu.istanbul/GiSoftGis/#/ezoning",
                   # Toplu enumerasyonda taranacak tapu (kadastro) mahalleleri.
                   # Beylikdüzü'nün tüm parselleri tek kadastro mahallesinde.
                   "mahalleler": ["KAVAKLI"]},
}

# ArcGIS KULLANIM kodları için yedek eşleme (domain yoksa).
_KULLANIM_FALLBACK = {
    1: "Konut", 2: "Ticaret", 3: "Konut + Ticaret", 4: "Sanayi", 5: "Turizm",
    6: "Yeşil Alan", 7: "Donatı", 8: "Resmi Kurum", 9: "Eğitim", 10: "Sağlık",
}

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36")

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
# Eski tek parça stok (geriye dönük okunur; yazım artık ilçe parçalarına yapılır).
_CACHE_PATH = os.path.join(_DATA_DIR, "imar_cache.json")
# İlçe başına ayrı stok dosyası: paralel ön-çekmede süreçler birbirini
# beklemez ve her yazım küçük kalır (tek parça dosya 12+ MB'a çıkıp her
# kayıtta baştan yazılıyordu -> tüm süreçler kilitte sıraya giriyordu).
_SHARD_DIR = os.path.join(_DATA_DIR, "imar")
_cache_lock = threading.Lock()


def _shard_path(dk: str) -> str:
    return os.path.join(_SHARD_DIR, f"{dk}.json")


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_cache() -> Dict[str, Any]:
    """Tüm stoku belleğe alır: önce eski tek parça dosya, sonra ilçe parçaları."""
    out: Dict[str, Any] = _read_json(_CACHE_PATH)
    try:
        for fn in os.listdir(_SHARD_DIR):
            if fn.endswith(".json"):
                out.update(_read_json(os.path.join(_SHARD_DIR, fn)))
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return out


_IMAR_CACHE: Dict[str, Any] = _load_cache()


def _save_district(dk: str) -> None:
    """Tek bir ilçenin kayıtlarını kendi parça dosyasına yazar.

    Parça dosyası kilit altında okunup birleştirilir (aynı ilçeye yazan ikinci
    bir süreç olursa kayıp olmasın), sonra atomik olarak değiştirilir. Farklı
    ilçeler farklı dosyalara yazdığı için süreçler birbirini beklemez."""
    try:
        os.makedirs(_SHARD_DIR, exist_ok=True)
        path = _shard_path(dk)
        pref = dk + "|"
        mine = {k: v for k, v in _IMAR_CACHE.items() if k.startswith(pref)}
        if not mine:
            return
        with open(path + ".lock", "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX)
            except Exception:
                pass
            merged = _read_json(path)
            merged.update(mine)
            _IMAR_CACHE.update(merged)
            tmp = f"{path}.{os.getpid()}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False)
            os.replace(tmp, path)
            try:
                fcntl.flock(lock, fcntl.LOCK_UN)
            except Exception:
                pass
    except Exception:
        pass


def _save_cache(district: Optional[str] = None) -> None:
    """Stoku diske yazar. İlçe verilirse yalnız o ilçenin parçası yazılır
    (toplu ön-çekmenin sıcak yolu); verilmezse bellekteki tüm ilçeler yazılır."""
    if district:
        _save_district(_norm(district))
        return
    for dk in {k.split("|", 1)[0] for k in _IMAR_CACHE if "|" in k}:
        _save_district(dk)


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
    "T.A.K.S": "taks", "K.A.K.S (Emsal)": "kaks", "K.A.K.S": "kaks",
    "K.A.K.S.": "kaks", "KAKS": "kaks", "Emsal": "emsal",
    "Ada/Parsel": "ada_parsel_belge", "Tapu Kütüğü": "tapu_kutugu",
    "Açıklama": "aciklama",
    "Ön Bahçe": "on_bahce", "Yan Bahçe": "yan_bahce", "Arka Bahçe": "arka_bahce",
    "Bina Derinliği": "bina_derinligi", "Bina Genişliği": "bina_genisligi",
    "Pafta": "pafta", "Mer'i İmar Planı": "imar_plani",
    "İdari Mahalle": "idari_mahalle", "Kot Alınacak Nokta": "kot_noktasi",
    "Tasdik Tarihi": "tasdik_tarihi", "Kısıtlama": "kisitlama",
}


def _clean_val(raw: str) -> str:
    # Ekranda görünmeyen/yardımcı öğeleri at (yazdırma dışı linkler, ikonlar,
    # sarı vurgulu uyarı notları) — asıl değer metnini KORUYARAK.
    raw = re.sub(r'<a\b[^>]*\bno-print\b[^>]*>.*?</a>', ' ', raw, flags=re.DOTALL | re.I)
    raw = re.sub(r'<marker\b[^>]*>.*?</marker>', ' ', raw, flags=re.DOTALL | re.I)
    raw = re.sub(r'<i\b[^>]*></i>', ' ', raw, flags=re.I)
    # Tooltip/span attribute leaks -> keep only real inner text.
    if "data-ref" in raw or "data-placement" in raw or "title=" in raw:
        inner = re.findall(r">([^<>]+)<", raw)
        if inner:
            raw = " ".join(inner)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", raw))
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\(\s*\)$", "", t).strip()          # boşalan parantezleri temizle
    if t in ("EMPTYROW", "-", ".", "", "- (-)", "-(-)"):
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
            # "509,94 m² ( Tapu alanı değildir! ) Bilgi" -> "509,94 m²"
            malan = re.match(r"\s*([\d.,]+\s*m²)", val)
            out["parsel_alani"] = malan.group(1) if malan else val.split("(")[0].strip()
        if label in _LABEL_MAP and val:
            out.setdefault(_LABEL_MAP[label], val)
        if val:
            tum[label] = val

    # Bazı belediyeler (ör. Pendik) "Plan Fonksiyon" hücresine önce genel bir
    # uyarı metni koyup asıl fonksiyonu sona yazıyor: "- Uygulama İmar Planına
    # ait genel plan notları ... Konut Alanı (509.941 m²)". Gerçek fonksiyonu ayır.
    fon = out.get("fonksiyon")
    if fon and len(fon) > 90:
        mf = re.search(r'([^.\-]{3,60}?\s*(?:Alanı|Alan|Bölgesi|Sahası)\s*(?:\([^)]*\))?)\s*$', fon)
        if mf:
            out["fonksiyon"] = mf.group(1).strip()
            out.setdefault("fonksiyon_aciklama", fon[:800])

    # Plan notları (numaralı liste) — tam metin.
    txt = _strip_html(doc)
    mnot = re.search(r"Plan Notlar[ıi][^0-9]{0,40}(1\s*-\s*.+?)(?:Yazd[ıi]r|Bu belge|©|$)", txt)
    if mnot:
        notes = re.sub(r"\s+", " ", mnot.group(1)).strip()
        if len(notes) > 30:
            out["plan_notlari"] = notes[:1500]

    # Plan notları ayrı bir PDF olarak linklenmişse (Pendik) URL'yi sakla.
    mpdf = re.search(r'https?://[^\s"\'<>]+/plannotlari/[^\s"\'<>]+\.pdf', doc, re.I)
    if mpdf:
        out["plan_notlari_pdf"] = _html.unescape(mpdf.group(0))

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

    # GiSoft: imar PDF'inden coğrafi koordinat (geometri poligonu yok, nokta var).
    if cfg["platform"] == "gisoft":
        try:
            rec = _query_gisoft(cfg, district, ada, parsel)
            if rec and rec.get("_lat") and rec.get("_lng"):
                o = 0.00035
                lat, lng = rec["_lat"], rec["_lng"]
                geom = {"type": "Polygon", "coordinates": [[
                    [lng - o, lat - o], [lng + o, lat - o],
                    [lng + o, lat + o], [lng - o, lat + o], [lng - o, lat - o]]]}
                return {"lat": lat, "lng": lng, "geometry": geom,
                        "tapu_mahalle": rec.get("tapu_mahalle", "")}
            return None
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


# ---------------------------------------------------------------------------
# NETCAD KEOS/YKR platformu (Pendik)
# ---------------------------------------------------------------------------
#   1) GET {proxy}/search?function=public.ykr_lsearch_parsel&q=ada/parsel
#        -> GeoJSON FeatureCollection; properties: {ad:"8100/13", mahalle, pk}
#           `pk` = imar belgesindeki `parselid`, geometry = parsel poligonu
#   2) GET {base}imar.aspx?parselid={pk}  -> NETGIS imar durumu belgesi (HTML)
#      (aynı divTable yapısı; `_extract_imar` ile ayrıştırılır)

def _keos_search(cfg: Dict[str, str], ada: str, parsel: str,
                 function: str = "public.ykr_lsearch_parsel") -> Optional[Dict[str, Any]]:
    """KEOS arama proxy'sinden ada/parsel için GeoJSON feature (tam eşleşme)."""
    r = requests.get(cfg["proxy"] + "/search",
                     params={"function": function, "q": f"{ada}/{parsel}"},
                     headers={"User-Agent": _UA, "Referer": cfg.get("kentrehberi", "")},
                     timeout=15, verify=False)
    feats = r.json().get("features", [])
    target = f"{ada}/{parsel}"
    for f in feats:
        if (f.get("properties") or {}).get("ad") == target:
            return f
    return None


def keos_list_ada(cfg: Dict[str, str], ada: str) -> list:
    """Bir ADA'daki tüm parselleri KEOS arama ucundan listeler -> ["ada/parsel"].

    DİKKAT: arama ucu ALT DİZE eşleşmesi yapar ve sorgu başına en fazla 50 kayıt
    döner. Küçük ada numaralarında ("1/") başka adaların parselleri ("8171/5")
    sonuçları doldurup gerçek eşleşmeleri dışarı itebilir; bu yüzden boş dönen
    adalar için çağıran taraf ucuz ada/parsel yoklamasına düşmelidir
    (bkz. bulk_fetch_netgis)."""
    proxy = cfg.get("search_proxy")
    if not proxy:
        return []
    try:
        r = requests.get(proxy + "/search",
                         params={"function": "public.ykr_lsearch_parsel", "q": f"{ada}/"},
                         headers={"User-Agent": _UA, "Referer": cfg.get("kentrehberi", "")},
                         timeout=15, verify=False)
        out = []
        for f in r.json().get("features", []):
            ad = (f.get("properties") or {}).get("ad") or ""
            if ad.startswith(f"{ada}/"):
                out.append(ad)
        return out
    except Exception:
        return []


def _geojson_centroid(geom: Optional[Dict[str, Any]]):
    """GeoJSON Polygon/MultiPolygon -> (lat, lng) dış halka ortalaması."""
    if not geom or not geom.get("coordinates"):
        return None
    try:
        if geom["type"] == "Polygon":
            ring = geom["coordinates"][0]
        elif geom["type"] == "MultiPolygon":
            ring = geom["coordinates"][0][0]
        else:
            return None
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return (sum(ys) / len(ys), sum(xs) / len(xs))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# GiSoft GIS platformu (Beylikdüzü) — anonim JWT + entity/report + PDF belgesi
# ---------------------------------------------------------------------------
#   1) GET  rest/application?applicationCode=...  -> `X-Auth-Token` yanıt başlığı
#            (her çağrı taze bir ANONİM JWT üretir; ayrı login gerekmez)
#   2) POST rest/entity/cache/list  {parcel, filterValue:"ada/parsel"} -> entity id
#   3) GET  rest/entity/report/parcel/2/{id}  -> ["ImarDurumuRaporu_<ts>.pdf"]
#   4) GET  rest/file/download/{ad}?isAttachment=false  (X-Auth-Token başlığı) -> PDF
#   5) PDF'ten TÜM alanları ayıkla (iki sütunlu anahtar/değer tablosu + koordinat)

def _gisoft_token(s: requests.Session, cfg: Dict[str, str]) -> Optional[str]:
    r = s.get(cfg["base"] + "/rest/application", params={"applicationCode": cfg["app"]},
              timeout=12, verify=False)
    return r.headers.get("x-auth-token") or r.headers.get("X-Auth-Token")


def _dms_to_dec(d: str, m: str, sec: str, hemi: str) -> float:
    v = int(d) + int(m) / 60.0 + float(sec) / 3600.0
    return round(-v if hemi in ("S", "W") else v, 6)


def _extract_gisoft_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """GiSoft imar durumu PDF'inden TÜM alanları ayıklar (iki sütunlu tablo +
    coğrafi koordinat + plan notları). pdfplumber kelime konumları ile."""
    import pdfplumber  # lazy: sadece gisoft ilçesinde gerekli
    out: Dict[str, Any] = {}
    tum: Dict[str, str] = {}
    try:
        pdf = pdfplumber.open(io.BytesIO(pdf_bytes))
    except Exception:
        return out

    alltext = " ".join((p.extract_text() or "") for p in pdf.pages)
    if "İmar Durumu Bilgisi bulunamadı" in alltext:
        out["imar_durumu_yok"] = True

    # Coğrafi koordinat (41°0'40"N 28°39'0"E) -> ondalık; konum snap için.
    mc = re.search(r'(\d+)°(\d+)\'([\d.]+)"?\s*([NS])\s+(\d+)°(\d+)\'([\d.]+)"?\s*([EW])', alltext)
    if mc:
        out["_lat"] = _dms_to_dec(mc.group(1), mc.group(2), mc.group(3), mc.group(4))
        out["_lng"] = _dms_to_dec(mc.group(5), mc.group(6), mc.group(7), mc.group(8))

    grid = next((p for p in pdf.pages if "İmar Durumu Bilgileri" in (p.extract_text() or "")), None)
    if grid is None:
        return out

    # Plan notları (grid'in üstündeki numaralı liste "1 - ... 2 - ...").
    gtext = grid.extract_text() or ""
    mnot = re.search(r'(1\s*-\s*.+?)(?:\d{2}/\d{2}/\d{4}\s+Tarihli İmar Durumu|Tarihli İmar Durumu)',
                     gtext, re.DOTALL)
    if mnot:
        notes = re.sub(r'\s+', ' ', mnot.group(1)).strip()
        if len(notes) > 30:
            out["plan_notlari"] = notes[:2000]

    rows: Dict[int, list] = {}
    for w in grid.extract_words():
        if w["top"] < 560:        # tablo, plan notlarının altında başlıyor
            continue
        k = round(w["top"] / 3) * 3
        rows.setdefault(k, []).append((w["x0"], w["text"]))

    def clean(v: str) -> str:
        v = re.sub(r"\s+", " ", v).strip()
        return "" if v in ("-", "*", "") else v

    # İki sütunlu tablo: sol değer kolonu x∈[188,300), sağ değer kolonu x≥455.
    LEFTMAP = {"Kat Adedi": "kat_adedi", "Taks": "taks", "Ön Bahçe Mesafesi": "on_bahce",
               "Arka Bahçe Mesafesi": "arka_bahce", "Hmaks": "hmaks", "Plan Ölçeği": "plan_olcegi"}
    RIGHTMAP = {"Maks Kat Adedi": "maks_kat_adedi", "Kaks": "kaks", "Emsal": "emsal",
                "Yan Bahçe Mesafesi": "yan_bahce", "İnşaat Nizamı": "insaat_nizami",
                "Tasdik Tarihi": "tasdik_tarihi"}

    for _, toks in sorted(rows.items()):
        toks = sorted(toks)
        line = " ".join(t for _, t in toks)
        # Başlık değer satırı: "MAHALLE PAFTA ADA PARSEL ALAN m²"
        if line.endswith("m²") and "Mahalle" not in line and "Fonksiyon" not in line:
            mh = re.match(r'^(.*?)\s+(\S+)\s+(\d+)\s+(\d+)\s+([\d.,]+)\s*m²$', line)
            if mh:
                out["tapu_mahalle"] = re.sub(r'\(.*?\)', '', mh.group(1)).strip()
                out["pafta"] = mh.group(2)
                out["ada_no"] = mh.group(3)
                out["parsel_no"] = mh.group(4)
                out["parsel_alani"] = mh.group(5) + " m²"
                tum["Mahalle"] = mh.group(1)
                continue
        if line.startswith("Plan Adı"):
            v = clean(line[len("Plan Adı"):])
            if v:
                out["plan_adi"] = v
                tum["Plan Adı"] = v
            continue
        if line.startswith("Fonksiyon Adı"):
            rest = re.sub(r'\s*-?\s*[\d.,]+\s*m²\s*$', '', line[len("Fonksiyon Adı"):])
            v = clean(rest.strip(" -"))
            if v:
                out["fonksiyon"] = v
                tum["Fonksiyon Adı"] = v
            continue
        if "İdari Mahalle" in line or line.startswith("KADASTRO") or line.startswith("Kapı"):
            continue
        # Genel eşli satır: sol/sağ etiket + değer.
        ll = " ".join(t for x, t in toks if x < 188).strip()
        lv = clean(" ".join(t for x, t in toks if 188 <= x < 300))
        rl = " ".join(t for x, t in toks if 300 <= x < 455).strip()
        rv = clean(" ".join(t for x, t in toks if x >= 455))
        if ll in LEFTMAP and lv:
            out[LEFTMAP[ll]] = lv
            tum[ll] = lv
        if rl in RIGHTMAP and rv:
            out[RIGHTMAP[rl]] = rv
            tum[rl] = rv

    if tum:
        out["tum_alanlar"] = tum
    return out


def _gisoft_parcel_id(s: requests.Session, cfg: Dict[str, str], tok: str,
                      ada: str, parsel: str) -> Optional[str]:
    body = {"entityAliasItemIndexMap": {"parcel": 0},
            "filterValue": f"{ada}/{parsel}", "maxResultCount": 20,
            "includeDeletedRecords": False}
    r = s.post(cfg["base"] + "/rest/entity/cache/list", data=json.dumps(body),
               headers={"X-Auth-Token": tok, "Content-Type": "application/json",
                        "Referer": cfg["base"] + "/"}, timeout=12, verify=False)
    lst = r.json().get("entityCacheModelList", [])
    if not lst:
        return None
    pref = f"{ada}/{parsel} "
    for e in lst:
        if e.get("entityAlias") == "parcel" and str(e.get("label", "")).startswith(pref):
            return e.get("id")
    return lst[0].get("id")


def _query_gisoft(cfg: Dict[str, str], district: str, ada: str, parsel: str) -> Optional[Dict[str, Any]]:
    s = requests.Session()
    s.headers.update({"User-Agent": _UA})
    tok = _gisoft_token(s, cfg)
    if not tok:
        return None
    eid = _gisoft_parcel_id(s, cfg, tok, ada, parsel)
    if not eid:
        return None
    hdr = {"X-Auth-Token": tok, "Referer": cfg["base"] + "/"}
    fn = s.get(cfg["base"] + f"/rest/entity/report/parcel/2/{eid}",
               headers=hdr, timeout=25, verify=False).json()
    if not isinstance(fn, list) or not fn:
        return None
    pdf = s.get(cfg["base"] + f"/rest/file/download/{fn[0]}",
                params={"isAttachment": "false"}, headers=hdr, timeout=25, verify=False)
    if pdf.status_code != 200 or "pdf" not in pdf.headers.get("content-type", ""):
        return None
    fields = _extract_gisoft_pdf(pdf.content)
    if not fields or (fields.get("imar_durumu_yok") and "fonksiyon" not in fields):
        # Parsel bir imar planı içinde değil (koordinat yine de dönebilir).
        if not fields.get("_lat"):
            return None
    return {
        "supported": True,
        "belediye": district.strip().title() + " Belediyesi",
        "ada_parsel": f"{ada}/{parsel}",
        "kaynak_url": cfg.get("eharita", ""),
        **fields,
    }


_ADAPTERS = {
    "netgis": _query_netgis,
    "arcgis_kentrehberi": _query_arcgis_kentrehberi,
    "gisoft": _query_gisoft,
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
    _save_cache(district)
    return stocked


def gisoft_list_all(district: str, mahalle_hint: str = "") -> list:
    """GiSoft ilçesindeki TÜM parselleri listeler -> [(entity_id, "ada/parsel"), ...].
    Arama ucu tek çağrıda binlerce kayıt döndürebiliyor; mahalle adı ile tarar."""
    cfg = MUNICIPAL_WEBGIS.get(_norm(district))
    if not cfg or cfg["platform"] != "gisoft":
        return []
    s = requests.Session()
    s.headers.update({"User-Agent": _UA})
    tok = _gisoft_token(s, cfg)
    if not tok:
        return []
    H = {"X-Auth-Token": tok, "Content-Type": "application/json",
         "Referer": cfg["base"] + "/"}
    hints = [mahalle_hint] if mahalle_hint else cfg.get("mahalleler", [])
    found: Dict[str, str] = {}
    for q in hints:
        body = {"entityAliasItemIndexMap": {"parcel": 0}, "filterValue": q,
                "maxResultCount": 20000, "includeDeletedRecords": False}
        try:
            r = s.post(cfg["base"] + "/rest/entity/cache/list", data=json.dumps(body),
                       headers=H, timeout=90, verify=False)
            for e in r.json().get("entityCacheModelList", []):
                m = re.match(r'^\s*(\d+)\s*/\s*(\d+)\s', e.get("label", ""))
                if m and e.get("id"):
                    found[str(e["id"])] = f"{m.group(1)}/{m.group(2)}"
        except Exception:
            continue
    return sorted(found.items(), key=lambda kv: kv[1])


def bulk_fetch_gisoft(district: str, delay: float = 1.0, limit: int = 0,
                      progress=None) -> int:
    """GiSoft ilçesi için TÜM parsellerin imar durumunu sırayla çekip stoklar.
    Her parsel için rapor üretimi + PDF indirme gerektiğinden hız sınırlıdır;
    devam edilebilir (stoktakiler atlanır). Stoklanan yeni kayıt sayısı döner."""
    cfg = MUNICIPAL_WEBGIS.get(_norm(district))
    if not cfg or cfg["platform"] != "gisoft":
        return 0
    targets = gisoft_list_all(district)
    if progress:
        progress("parsel listesi: %d" % len(targets))

    s = requests.Session()
    s.headers.update({"User-Agent": _UA})
    tok = _gisoft_token(s, cfg)
    stocked = done = 0
    for eid, ap in targets:
        if limit and done >= limit:
            break
        ada, parsel = ap.split("/", 1)
        key = _cache_key(district, ada, parsel)
        if key in _IMAR_CACHE:
            continue
        done += 1
        try:
            hdr = {"X-Auth-Token": tok, "Referer": cfg["base"] + "/"}
            fn = s.get(cfg["base"] + f"/rest/entity/report/parcel/2/{eid}",
                       headers=hdr, timeout=30, verify=False)
            if fn.status_code == 401:                      # token süresi doldu -> tazele
                tok = _gisoft_token(s, cfg)
                hdr = {"X-Auth-Token": tok, "Referer": cfg["base"] + "/"}
                fn = s.get(cfg["base"] + f"/rest/entity/report/parcel/2/{eid}",
                           headers=hdr, timeout=30, verify=False)
            names = fn.json()
            if not isinstance(names, list) or not names:
                continue
            pdf = s.get(cfg["base"] + f"/rest/file/download/{names[0]}",
                        params={"isAttachment": "false"}, headers=hdr,
                        timeout=30, verify=False)
            if pdf.status_code != 200 or "pdf" not in pdf.headers.get("content-type", ""):
                continue
            fields = _extract_gisoft_pdf(pdf.content)
            if not fields:
                continue
            rec = {"supported": True,
                   "belediye": district.strip().title() + " Belediyesi",
                   "ada_parsel": ap, "kaynak_url": cfg.get("eharita", ""), **fields}
            with _cache_lock:
                _IMAR_CACHE[key] = rec
            stocked += 1
            if progress and stocked % 25 == 0:
                progress("stoklandı: %d / denenen %d" % (stocked, done))
            if stocked % 100 == 0:
                _save_cache(district)
        except Exception:
            pass
        time.sleep(delay)
    _save_cache(district)
    return stocked


def netgis_probe_ada(cfg: Dict[str, str], ada: str, parsel_max: int = 40,
                     delay: float = 0.15) -> list:
    """Bir adadaki parselleri UCUZ yoklama ile bulur -> ["ada/parsel"].

    imarsvc.aspx `type=adaparsel` yanıtı ~80 bayt ve olmayan parsel için boş
    dizi döner; ağır (yüzlerce KB) imar belgesi indirilmez. Arama ucunun
    yetersiz kaldığı adalar için yedek yol."""
    base = cfg["base"]
    out = []
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": _UA})
        s.get(base, timeout=10, verify=False)
        nonce = s.cookies.get("svc_nonce") or ""
        h = {"Referer": base, "X-Service-Nonce": nonce, "X-Requested-With": "XMLHttpRequest"}
        miss = 0
        for p in range(1, parsel_max + 1):
            r = s.get(base + "service/imarsvc.aspx",
                      params={"type": "adaparsel", "adaparsel": f"{ada}/{p}"},
                      headers=h, timeout=10, verify=False)
            arr = r.json() if r.text.strip().startswith("[") else []
            if arr:
                out.append(f"{ada}/{p}")
                miss = 0
            else:
                miss += 1
                if miss >= 12 and not out:
                    break          # ada hiç yok gibi -> erken çık
            time.sleep(delay)
    except Exception:
        pass
    return out


_SCAN_KEY = "__scan_oid__"   # işaret anahtarı: "{ilce}|__scan_oid__"


def bulk_fetch_netgis_oid(district: str, start: int = 0, end: int = 250000,
                          delay: float = 0.4, limit: int = 0,
                          miss_stop: int = 3000, progress=None) -> int:
    """NETGIS ilçesini PARSEL KİMLİĞİ (OBJECTID) üzerinden tarayarak stoklar.

    NETGIS'te ada/parsel'i toplu listeleyen bir uç YOK; ada×parsel kombinasyonu
    denemek ise ıskadan ibaret. Onun yerine parselid 1..N taranır:

      1) service/imarsvc.aspx?type=parsel&parselid=N   (~250 bayt, hızlı)
         -> ADAPARSEL var mı? Yoksa/zaten stoktaysa AĞIR belge indirilmez.
      2) imar.aspx?parselid=N                          (~100-400 KB)
         -> tüm imar alanları; ada/parsel belgeden okunur.

    Kaldığı yerden devam eder (stokta `__scan_oid__|ilce` işareti tutulur).
    Üst üste `miss_stop` boş kimlikten sonra taramayı bitirir.
    """
    cfg = MUNICIPAL_WEBGIS.get(_norm(district))
    if not cfg or cfg["platform"] != "netgis":
        return 0
    base = cfg["base"]
    dk = _norm(district)
    mark = f"{dk}|{_SCAN_KEY}"
    if not start:
        start = int(_IMAR_CACHE.get(mark, {}).get("last_oid", 0)) + 1

    s = requests.Session()
    s.headers.update({"User-Agent": _UA})

    def _nonce():
        s.get(base, timeout=10, verify=False)
        return s.cookies.get("svc_nonce") or ""

    nonce = _nonce()
    h = {"Referer": base, "X-Service-Nonce": nonce, "X-Requested-With": "XMLHttpRequest"}
    stocked = miss = done = 0
    oid = start
    while oid <= end:
        if limit and done >= limit:
            break
        try:
            r = s.get(base + "service/imarsvc.aspx",
                      params={"type": "parsel", "parselid": oid},
                      headers=h, timeout=12, verify=False)
            txt = r.text.strip()
            if txt.startswith("#") or r.status_code == 403:       # nonce düştü -> tazele
                nonce = _nonce()
                h["X-Service-Nonce"] = nonce
                continue
            arr = json.loads(txt) if txt.startswith("[") else []
            ap = (arr[0].get("ADAPARSEL") or "").strip() if arr else ""
            m = re.match(r'^\s*(\d+)\s*/\s*(\d+)\s*$', ap)
            if not m:
                miss += 1
                if miss >= miss_stop:
                    if progress:
                        progress("üst üste %d boş kimlik -> tarama bitti (oid=%d)" % (miss, oid))
                    break
                oid += 1
                continue
            miss = 0
            ada, parsel = m.group(1), m.group(2)
            key = _cache_key(district, ada, parsel)
            if key not in _IMAR_CACHE:
                done += 1
                doc = s.get(base + "imar.aspx", params={"parselid": oid},
                            headers={"Referer": base, "X-Service-Nonce": nonce},
                            timeout=30, verify=False).text
                fields = _extract_imar(doc)
                if fields:
                    rec = {"supported": True,
                           "belediye": district.strip().title() + " Belediyesi",
                           "ada_parsel": f"{ada}/{parsel}",
                           "tapu_mahalle": (arr[0].get("TAPU_MAH_ADI") or ""),
                           "kaynak_url": f"{base}imar.aspx?parselid={oid}", **fields}
                    geom = arr[0].get("POLY")
                    if geom:
                        try:
                            cen = _geojson_centroid(json.loads(geom))
                            if cen:
                                rec["_lat"], rec["_lng"] = cen
                        except Exception:
                            pass
                    with _cache_lock:
                        _IMAR_CACHE[key] = rec
                    stocked += 1
                    if progress and stocked % 25 == 0:
                        progress("stoklandı: %d (oid=%d, %s/%s)" % (stocked, oid, ada, parsel))
                    if stocked % 100 == 0:
                        _IMAR_CACHE[mark] = {"last_oid": oid}
                        _save_cache(district)
                time.sleep(delay)
        except Exception:
            pass
        oid += 1
    _IMAR_CACHE[mark] = {"last_oid": oid}
    _save_cache(district)
    return stocked


def bulk_fetch_netgis(district: str, adalar, delay: float = 0.8, limit: int = 0,
                      probe: bool = True, progress=None) -> int:
    """NETGIS ilçesi için verilen ADA listesindeki tüm parselleri stoklar.
    Pendik'te parsel listesi önce KEOS arama ucundan alınır; arama ucu boş
    dönerse (alt-dize/50 kayıt sınırı) ucuz ada/parsel yoklamasına düşülür."""
    cfg = MUNICIPAL_WEBGIS.get(_norm(district))
    if not cfg or cfg["platform"] != "netgis":
        return 0
    stocked = done = 0
    for ada in adalar:
        if limit and done >= limit:
            break
        ada = str(ada)
        aps = keos_list_ada(cfg, ada) if cfg.get("search_proxy") else []
        if not aps and probe:
            aps = netgis_probe_ada(cfg, ada)
        for ap in aps:
            if limit and done >= limit:
                break
            a, p = ap.split("/", 1)
            key = _cache_key(district, a, p)
            if key in _IMAR_CACHE:
                continue
            done += 1
            res = fetch_imar_durumu(district, a, p)
            if res:
                stocked += 1
                if progress and stocked % 20 == 0:
                    progress("stoklandı: %d / denenen %d (ada %s)" % (stocked, done, ada))
            time.sleep(delay)
    _save_cache(district)
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
            _save_cache(district)
    return result
