"""Geocoded fiyat gözlem defteri — mahalle İÇİ konum çarpanının TEK gerçekçi kaynağı.

NEDEN VAR:
İstanbul'da mahalleler geniş ve heterojen; aynı mahallede kıyıya 200 m mesafedeki
daire ile 1,5 km içerideki daire aynı m² fiyatına sahip değil. Bunu ölçebilmek
için KOORDİNATLI fiyat gözlemi gerekiyor. Denenen ve ELENEN yollar:

  * EmlakJet / diğer hazır GitHub veri setleri -> koordinat YOK (yalnız
    "İstanbul - İlçe - Mahalle" metni). 93 bin satırlık set dahil kontrol edildi.
  * EmlakJet canlı  -> robots.txt harita görünümünü, get_detail'i ve mahalle
    filtresini açıkça yasaklıyor.
  * sahibinden / hepsiemlak / hürriyetemlak -> Cloudflare, robots.txt dahil 403.
  * Coğrafyadan çıkarım (kıyı/metro/rakım) -> ilçe İÇİ kıyı gradyanı ölçülemedi:
    30 ilçenin 14'ünde negatif 16'sında pozitif, medyan etki %2. Beşiktaş -0.75
    iken Sarıyer +1.63 (aynı Boğaz, zıt işaret) -> gradyan değil gürültü.
    Bu yüzden coğrafi çarpan ÜRETİLMEDİ (sahte hassasiyet olurdu).

GERİYE KALAN TEK SAĞLAM YOL: kendi kullanıcılarımızın talepleri. Her ekspertiz
isteğinde elimizde adres + istenen fiyat + m² var ve adresi TKGM ile zaten
PARSEL KOORDİNATINA çözüyoruz. Yani her talep bir geocoded fiyat gözlemi.
Bunlar biriktikçe mahalle içi konum çarpanı GERÇEK veriyle kestirilebilir —
hiçbir scraper'ın yasal olarak veremeyeceği veri.

Kayıt JSONL olarak tutulur (append-only, eşzamanlı yazıma dayanıklı).
Kişisel veri saklanmaz: kapı/daire no ve serbest metin adres YAZILMAZ;
yalnız parsel koordinatı, ada/parsel, ilçe/mahalle ve ilan nitelikleri.
"""
import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fiyat_gozlemleri.jsonl")
_lock = threading.Lock()


def kaydet(*, lat: Optional[float], lng: Optional[float],
           district: Optional[str], neighborhood: Optional[str],
           price: Optional[float], net_m2: Optional[float],
           building_age: Optional[int] = None,
           floor_category: Optional[str] = None,
           ada_no: Optional[str] = None, parsel_no: Optional[str] = None,
           kaynak: str = "ekspertiz_talebi") -> bool:
    """Bir fiyat gözlemini deftere ekler. Koordinat veya fiyat yoksa yazmaz.

    KİŞİSEL VERİ YAZILMAZ — kapı no, daire no, serbest adres ve kullanıcı
    bilgisi bilinçli olarak dışarıda bırakılmıştır."""
    if not lat or not lng or not price or not net_m2 or net_m2 <= 0:
        return False
    try:
        rec = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lat": round(float(lat), 6),
            "lng": round(float(lng), 6),
            "ilce": (district or "").strip(),
            "mahalle": (neighborhood or "").strip(),
            "fiyat": float(price),
            "net_m2": float(net_m2),
            "tlm2": round(float(price) / float(net_m2), 2),
            "bina_yasi": building_age,
            "kat": floor_category,
            "ada": (str(ada_no).strip() if ada_no else None),
            "parsel": (str(parsel_no).strip() if parsel_no else None),
            "kaynak": kaynak,
        }
        line = json.dumps(rec, ensure_ascii=False)
        with _lock:
            os.makedirs(os.path.dirname(_PATH), exist_ok=True)
            with open(_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        return True
    except Exception:
        return False      # gözlem defteri ekspertizi asla bozmamalı


def ozet() -> Dict[str, Any]:
    """Deftere kaç gözlem birikti, mahalle içi kestirim için yeterli mi."""
    n = 0
    mah: Dict[str, int] = {}
    try:
        with open(_PATH, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                n += 1
                k = f"{r.get('ilce')}|{r.get('mahalle')}"
                mah[k] = mah.get(k, 0) + 1
    except FileNotFoundError:
        pass
    # Mahalle içi konum gradyanı için mahalle başına ~40+ koordinatlı gözlem gerekir.
    hazir = sum(1 for v in mah.values() if v >= 40)
    return {"gozlem": n, "mahalle": len(mah), "kestirime_hazir_mahalle": hazir,
            "esik": 40}
