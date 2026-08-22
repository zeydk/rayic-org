#!/usr/bin/env python3
"""İmar durumu ön-çekme (pre-warm) aracı — belediyelerden imar verisini önceden
çekip yerel stoka (data/imar_cache.json) yazar; böylece son kullanıcı sorgusu
anında (0 sn) cevaplanır.

GERÇEKÇİ NOT:
  Bir ilçenin TÜM parsellerini (on binlerce) tek seferde çekmek pratik değildir
  (süre + belediye sunucusuna aşırı yük / IP engeli riski). Bu araç:
    * hız sınırlı (rate-limited) ve nazik çalışır,
    * devam edebilir (resumable): zaten stokta olanı atlar,
    * verilen ada aralığı VEYA bir ada/parsel listesi dosyası için çalışır.
  Öneri: yoğun mahalleleri / elinizdeki ilan portföyünün parsellerini önceden
  stoklayın; gerisi zaten talep geldikçe (cache-on-demand) birikir.

Kullanım:
  # ada 1..2000, her ada için parsel 1..40 (nazik, 0.8 sn ara):
  python -m scripts.prewarm_imar --district Kadıköy --ada 1-2000 --parsel 1-40 --delay 0.8

  # bir dosyadan (her satır: "ada/parsel"):
  python -m scripts.prewarm_imar --district Maltepe --file parseller.txt --delay 0.8
"""
import argparse
import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.imar_service import (  # noqa: E402
    fetch_imar_durumu, bulk_fetch_arcgis, _cache_key, _IMAR_CACHE, MUNICIPAL_WEBGIS, _norm,
)


def _parse_range(spec: str):
    if "-" in spec:
        a, b = spec.split("-", 1)
        return range(int(a), int(b) + 1)
    return range(int(spec), int(spec) + 1)


def iter_targets(args):
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "/" in line:
                    ada, parsel = line.split("/", 1)
                    yield ada.strip(), parsel.strip()
    else:
        for ada in _parse_range(args.ada):
            for parsel in _parse_range(args.parsel):
                yield str(ada), str(parsel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--district", required=True)
    ap.add_argument("--ada", default="1-1000", help="ada aralığı, örn 1-2000")
    ap.add_argument("--parsel", default="1-40", help="parsel aralığı, örn 1-40")
    ap.add_argument("--file", help="satır başına 'ada/parsel' içeren dosya")
    ap.add_argument("--delay", type=float, default=0.8, help="istekler arası saniye")
    ap.add_argument("--limit", type=int, default=0, help="max deneme (0=sınırsız)")
    args = ap.parse_args()

    cfg = MUNICIPAL_WEBGIS.get(_norm(args.district))
    if not cfg:
        print(f"[!] {args.district} desteklenen ilçelerde değil. Desteklenen: {sorted(MUNICIPAL_WEBGIS)}")
        return

    # ArcGIS ilçelerinde TOPLU (spatial-join) mod — çok hızlı, ıskasız.
    if cfg["platform"] == "arcgis_kentrehberi":
        print(f"[ArcGIS toplu mod] {args.district} — tüm parseller + plan adaları çekiliyor...")
        n = bulk_fetch_arcgis(args.district, progress=lambda m: print("  " + m, flush=True))
        print(f"\nBitti. {args.district}: {n} parsel stoklandı | Toplam stok={len(_IMAR_CACHE)}")
        return

    tried = hit = skipped = 0
    for ada, parsel in iter_targets(args):
        if args.limit and tried >= args.limit:
            break
        tried += 1
        key = _cache_key(args.district, ada, parsel)
        if key in _IMAR_CACHE:
            skipped += 1
            continue
        res = fetch_imar_durumu(args.district, ada, parsel)  # canlı çeker + stoklar
        if res:
            hit += 1
            print(f"  ✓ {ada}/{parsel}: {res.get('fonksiyon','?')}  (stok: {len(_IMAR_CACHE)})")
        time.sleep(args.delay)  # belediye sunucusuna nazik davran
    print(f"\nBitti. Denenen={tried} Bulunan={hit} Atlanan(stokta)={skipped} | Toplam stok={len(_IMAR_CACHE)}")


if __name__ == "__main__":
    main()
