"""Mahalle İÇİ konum fiyat çarpanı — ÖLÇÜLMÜŞ katsayılarla.

NE YAPAR: Bir konutun koordinatını alır, aynı mahalledeki ORTALAMA konuma göre
fiyat çarpanını döndürür. Çarpan mahalle ortalamasında 1.00'dir ve GÖRELİdir:
mahallenin m² ortalaması ileride değişse bile çarpan geçerliliğini korur.

    carpan = exp( b · ( x_konut − x_mahalle ) )

KATSAYILAR NEREDEN: Uydurma değil, ölçüm. EmlakJet'ten toplanan koordinatlı
ilan örnekleminde mahalle sabit etkili regresyon (scripts/estimate_location_factor.py):

    log(TL/m²) = mahalle_sabit_etkisi + b·konum + c·daire_ozellikleri

Mahalle sabit etkisi mahallenin fiyat seviyesini soğurduğu için `b` yalnızca
MAHALLE İÇİ değişimden gelir. Daire özellikleri (m², yaş, oda) kontrol edilir.

ÖLÇÜM SONUCU — NİHAİ (7009 ilan, 231 mahalle; 20 ilçelik örneklem tamamlandı):
    ln_d_kiyi = -0.245 -> kıyıya uzaklık 2 katına çıkınca fiyat ~%16 DÜŞER
    ln_d_ray  = -0.109 -> raylı sisteme (metro+Marmaray) uzaklık 2x -> ~%7 düşer

SAĞLAMLIK (nihai örneklem):
  * Bir mahalle çıkarma: kıyı 231/231 mahallede NEGATİF (-0.282..-0.113);
    raylı da 231/231 negatif (-0.156..-0.054).
  * Bootstrap %5-%95: kıyı (-0.329, -0.183), raylı (-0.170, -0.036) —
    ikisi de sıfırı İÇERMEZ.
  * Örneklem dışı hata iyileşiyor (MAE 0.3082 -> 0.3070).

YAKINSAMA: Katsayı örneklem büyüdükçe oturdu ve kararlı hale geldi:
    n=2554 -> -0.193 | n=3639 -> -0.234 | n=7009 -> -0.245
Ara aşamada havuzlanmış tahmin -0.404'e sıçramıştı; bunun aykırı değerden
DEĞİL örneklem bileşiminden (önce pahalı kıyı ilçeleri) kaynaklandığı
tespit edildi (%1-%2 winsorize katsayıyı değiştirmiyordu). Bu yüzden
tahminci artık mahalle-içi eğim medyanıyla çapraz kontrol yapıp
MUHAFAZAKÂR olanı seçiyor.

ÖNCEKİ BAŞARISIZ DENEME (kayıt için): Aynı etki mahalle MERKEZLERİ üzerinden
kestirilmeye çalışıldığında ilçe içi kıyı katsayısı -0.02 (gürültü) çıkmıştı;
30 ilçenin 14'ünde negatif 16'sında pozitifti. Fark, şimdi mahalle İÇİ gerçek
ilan koordinatlarıyla ölçüyor olmamız.

DÜRÜST SINIRLAR:
  * Örneklem konumları 462 m ızgaraya yuvarlı -> ölçüm hatası katsayıyı sıfıra
    çeker; gerçek etki muhtemelen ölçtüğümüzden BÜYÜKTÜR (alt sınır).
  * Katsayı 231 mahalleden kestirilip tüm İstanbul'a uygulanıyor.
  * Konumun kontrollerden SONRAKİ ek açıklaması küçük (~%1); yani konum
    gerçek ama fiyatın küçük bir bölümünü açıklıyor — piyasada modellenemeyen
    başka etkenler baskın.
  * Çarpan sınırlandırılır (0.70-1.40) ve sonuç TAHMİN olarak etiketlenir.
"""
import json
import math
import os
from typing import Any, Dict, Optional

_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "konum_carpani.json")


def _load() -> Dict[str, Any]:
    try:
        with open(_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_M = _load()
META: Dict[str, Any] = _M.get("meta", {})
_B: Dict[str, float] = _M.get("katsayilar", {})
def _load_kiyi():
    """GERCEK kiyi cizgisi (OSM natural=coastline, ~80 m izgara, 3580 nokta)."""
    try:
        with open(os.path.join(os.path.dirname(__file__), "..", "data",
                               "kiyi_cizgisi.json"), encoding="utf-8") as f:
            return [tuple(p) for p in json.load(f)]
    except Exception:
        return []


_KIYI = _load_kiyi()
_RAY = _M.get("rayli_duraklar") or []
_MERKEZ = _M.get("mahalle_merkezleri") or {}
_ILCE = _M.get("ilce_merkezleri") or {}


def _nrm(s: Optional[str]) -> str:
    s = (s or "").strip().lower()
    for a, b in (("ı", "i"), ("İ", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"),
                 ("ö", "o"), ("ç", "c"), ("â", "a"), ("-", " ")):
        s = s.replace(a, b)
    return " ".join(s.split())


def _km(a: float, b: float, c: float, d: float) -> float:
    return math.hypot((a - c) * 111.0,
                      (b - d) * 111.0 * math.cos(math.radians((a + c) / 2.0)))


def _d_kiyi(lat: float, lng: float) -> float:
    return min(_km(lat, lng, p[0], p[1]) for p in _KIYI) if _KIYI else 0.0


def _d_ray(lat: float, lng: float) -> float:
    return min(_km(lat, lng, p[0], p[1]) for p in _RAY) if _RAY else 0.0


def mahalle_merkezi(district: Optional[str], neighborhood: Optional[str],
                    lat: Optional[float] = None, lng: Optional[float] = None):
    """Mahallenin referans merkezi (aynı adlı mahalleler için doğru olanı seçer).

    İstanbul'da çok sayıda mahalle aynı adı taşıyor ("Merkez" 11 yerde, "Maden"
    2 yerde...). Önceden ilçe adı mahalle listesinde yoksa İLK aday seçiliyordu
    ve yanlış konuma düşebiliyordu (Esenyurt/Merkez gerçek yerden 7 km uzağa).
    Artık sırayla: (1) konutun kendi koordinatına en yakın aday, (2) İLÇE
    merkezine en yakın aday, (3) tek aday varsa o."""
    cands = _MERKEZ.get(_nrm(neighborhood))
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    if lat is not None and lng is not None:
        return min(cands, key=lambda p: _km(p[0], p[1], lat, lng))
    ic = _ILCE.get(_nrm(district))
    if ic:
        return min(cands, key=lambda p: _km(p[0], p[1], ic[0], ic[1]))
    return cands[0]


def konum_carpani(lat: Optional[float], lng: Optional[float],
                  district: Optional[str], neighborhood: Optional[str],
                  alt: float = 0.70, ust: float = 1.40) -> Optional[Dict[str, Any]]:
    """Konutun mahalle ortalamasına göre konum çarpanı (1.00 = mahalle ortalaması)."""
    if lat is None or lng is None or not _B:
        return None
    ref = mahalle_merkezi(district, neighborhood, lat, lng)
    if not ref:
        return None

    bk = float(_B.get("ln_d_kiyi", 0.0))
    br = float(_B.get("ln_d_ray", 0.0))
    pk, pr = _d_kiyi(lat, lng), _d_ray(lat, lng)
    mk, mr = _d_kiyi(ref[0], ref[1]), _d_ray(ref[0], ref[1])

    z = bk * (math.log1p(pk) - math.log1p(mk)) + br * (math.log1p(pr) - math.log1p(mr))
    ham = math.exp(z)
    carpan = max(alt, min(ust, ham))

    if pk < mk:
        yon = "mahalle ortalamasından kıyıya DAHA YAKIN"
    elif pk > mk:
        yon = "mahalle ortalamasından kıyıya DAHA UZAK"
    else:
        yon = "mahalle ortalamasıyla aynı"
    return {
        "carpan": round(carpan, 3),
        "carpan_ham": round(ham, 3),
        "sinirlandi": abs(ham - carpan) > 1e-9,
        "konut_kiyi_km": round(pk, 2), "mahalle_kiyi_km": round(mk, 2),
        "konut_ray_km": round(pr, 2), "mahalle_ray_km": round(mr, 2),
        "yon": yon,
        "tahmin": True,
        "dayanak": ("%s ilan / %s mahallelik koordinatlı örneklemden ölçüldü"
                    % (META.get("ornek_n", "?"), META.get("mahalle_n", "?"))),
    }
