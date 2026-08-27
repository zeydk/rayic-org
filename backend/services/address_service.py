"""İBB e-Plan resmî adres sistemi — ilçe → mahalle → sokak → kapı → koordinat.

NEDEN: Kullanıcıya serbest metin adres yazdırmak baştan beri en kırılgan
halkaydı; adres ayrıştırma yanlış ada/parsel veya yanlış konum üretebiliyordu.
İBB e-Plan (eplan.ibb.istanbul) İstanbul'un RESMÎ adres ağacını açık bir uçtan
sunuyor ve kapı numarası seviyesinde KOORDİNAT veriyor. Böylece:

  * Kullanıcı adres YAZMAZ, listeden SEÇER (uydurma/eksik adres sorunu biter).
  * Konum tahmin edilmez; binanın kendi koordinatı gelir.
  * Koordinattan parsel (ada/parsel) kesin çözülür.

Doğrulandı: Caddebostan/18 Mart Sk. kapı "1" -> 40.97146,29.05144 -> TKGM
ada 1150 parsel 35 "Bahçeli Kargir Apartman"; kapı "11A" -> ada 1150 parsel 88.
Farklı kapılar farklı gerçek binalara düşüyor.

Uçlar (POST, JSON):
    /backend/ilce      {}                          -> [{id,name}]
    /backend/mahalle   {id: ilceId}                -> [{id,name}]
    /backend/sokak     {id: mahalleId}             -> [{id,name}]
    /backend/kapi      {districtId, id: sokakId}   -> [{id,name,geometry{x,y}}]
    /backend/getbypoint {x,y}                      -> parsel (ADA/PARSEL/TAPUMAHADI)
    /backend/getbyadaparsel {ilce,ada,parsel}      -> parsel

Koordinatlar Web Mercator (EPSG:3857); WGS84'e çevrilir.

NOT: Uygulamanın yol öneki (ör. /uWxvrTpLQ/) derleme ile değişebilir; sabit
değer çalışmazsa ana sayfadan otomatik yeniden keşfedilir.
"""
import math
import re
import threading
from typing import Any, Dict, List, Optional

import requests

ROOT = "https://eplan.ibb.istanbul"
_DEFAULT_PREFIX = "/uWxvrTpLQ/backend"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
_HDR = {"User-Agent": _UA, "Content-Type": "application/json",
        "Referer": ROOT + "/sorgu/plansorgu"}

_prefix = _DEFAULT_PREFIX
_lock = threading.Lock()
_cache: Dict[str, Any] = {}


def mercator_to_wgs84(x: float, y: float):
    """EPSG:3857 -> (lat, lng)."""
    lon = x / 20037508.34 * 180.0
    lat = math.degrees(2 * math.atan(math.exp(y / 20037508.34 * math.pi)) - math.pi / 2)
    return round(lat, 7), round(lon, 7)


def _discover_prefix() -> Optional[str]:
    """Uygulama yol öneki değiştiyse ana sayfadan yeniden bul."""
    try:
        html = requests.get(ROOT + "/sorgu/plansorgu", headers={"User-Agent": _UA},
                            timeout=15).text
        m = re.search(r'src="(?:\./)?(main\.[a-f0-9]+\.js)"', html)
        if not m:
            return None
        js = requests.get(f"{ROOT}/sorgu/{m.group(1)}", headers={"User-Agent": _UA},
                          timeout=45).text
        mm = re.search(r'["\'](/[A-Za-z0-9_-]{6,20}/backend)["\']', js)
        return mm.group(1) if mm else None
    except Exception:
        return None


def _post(path: str, body: Dict[str, Any]) -> Any:
    global _prefix
    for attempt in (1, 2):
        try:
            r = requests.post(f"{ROOT}{_prefix}/{path}", json=body, headers=_HDR, timeout=20)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        if attempt == 1:                      # önek değişmiş olabilir -> keşfet
            np = _discover_prefix()
            if np and np != _prefix:
                with _lock:
                    _prefix = np
                continue
        break
    return None


def ilceler() -> List[Dict[str, Any]]:
    if "ilce" not in _cache:
        _cache["ilce"] = _post("ilce", {}) or []
    return _cache["ilce"]


def mahalleler(ilce_id: int) -> List[Dict[str, Any]]:
    k = f"mah:{ilce_id}"
    if k not in _cache:
        _cache[k] = _post("mahalle", {"id": int(ilce_id), "geometry": False}) or []
    return _cache[k]


def sokaklar(mahalle_id: int) -> List[Dict[str, Any]]:
    k = f"sok:{mahalle_id}"
    if k not in _cache:
        _cache[k] = _post("sokak", {"id": int(mahalle_id), "geometry": False}) or []
    return _cache[k]


def kapilar(mahalle_id: int, sokak_id: int) -> List[Dict[str, Any]]:
    """Sokaktaki kapılar + her birinin WGS84 koordinatı."""
    k = f"kapi:{mahalle_id}:{sokak_id}"
    if k in _cache:
        return _cache[k]
    raw = _post("kapi", {"districtId": int(mahalle_id), "id": int(sokak_id)}) or []
    out = []
    for d in raw:
        g = d.get("geometry") or {}
        rec = {"id": d.get("id"), "name": d.get("name")}
        if g.get("x") is not None:
            rec["lat"], rec["lng"] = mercator_to_wgs84(g["x"], g["y"])
        out.append(rec)
    _cache[k] = out
    return out


def parsel_by_point(lat: float, lng: float) -> Optional[Dict[str, Any]]:
    """Koordinattan İBB parsel kaydı (ada/parsel/tapu mahalle + poligon)."""
    x = lng / 180.0 * 20037508.34
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0) \
        * 20037508.34 / 180.0
    j = _post("getbypoint", {"x": x, "y": y})
    feats = (j or {}).get("features") or []
    if not feats:
        return None
    a = feats[0].get("attributes") or {}
    out = {"ada": a.get("ADA"), "parsel": a.get("PARSEL"),
           "tapu_mahalle": a.get("TAPUMAHADI")}
    rings = (feats[0].get("geometry") or {}).get("rings")
    if rings:
        out["geometry"] = {"type": "Polygon", "coordinates": [
            [[p[1], p[0]] for p in
             ([list(mercator_to_wgs84(px, py)) for px, py in rings[0]])]]}
    return out


def adres_coz(ilce_id: int, mahalle_id: int, sokak_id: int,
              kapi_id: int) -> Optional[Dict[str, Any]]:
    """Seçilen kapı için koordinat + ada/parsel. Wizard'ın kullandığı uç."""
    for k in kapilar(mahalle_id, sokak_id):
        if str(k.get("id")) == str(kapi_id):
            if k.get("lat") is None:
                return None
            out = {"lat": k["lat"], "lng": k["lng"], "kapi_no": k.get("name")}
            p = parsel_by_point(k["lat"], k["lng"])
            if p:
                out.update({"ada_no": p.get("ada"), "parsel_no": p.get("parsel"),
                            "tapu_mahalle": p.get("tapu_mahalle")})
            return out
    return None
