#!/usr/bin/env python3
"""Mahalle İÇİ konum örneklemi — koordinatlı ilan toplayıcı (EmlakJet).

AMAÇ: Mahalle içi konum fiyat çarpanını GERÇEK veriyle kestirebilmek. Bunun için
koordinatlı fiyat gözlemi gerekiyor; hazır veri setlerinin hiçbirinde koordinat
yok (yalnız "İlçe - Mahalle" metni).

KONUM NEREDEN GELİYOR: İlan sayfasındaki harita, ilana özel karo (tile) URL'leri
yüklüyor: .../MapServer/tile/16/{row}/{col}. 2x2 karo bloğunun ortak köşesi
harita merkezidir. Zoom 16'da karo ~460 m, yani konum ~460 m ızgaraya
yuvarlanmış olarak elde edilir — bina hassasiyeti DEĞİL, ama mahalle içi
(1-3 km) ayrışma için yeterli.
Doğrulandı: aynı mahalledeki (Erenköy) 4 ilan 4 FARKLI merkez verdi
(460-1029 m arayla) -> harita ilana özel, mahalleye sabitlenmiş değil.

KURALLARA UYUM (bilerek ve açıkça):
  * Yalnız robots.txt'in İZİN VERDİĞİ yollar çekilir: /satilik-konut/... gezinme
    ve /ilan/... detay sayfaları. EmlakJet'in YASAKLADIĞI yollara HİÇ
    dokunulmaz: harita görünümü (view_type=map, gorunum=harita), /get_detail/*,
    /listings/*, mahalle filtresi (?mahalle), ?q=, ?filtreler=.
  * Varsayılan 3 sn bekleme, tek akış (paralel yok).
  * 403/429/CAPTCHA görülürse ANINDA durur; korumayı aşmaya çalışmaz
    (UA rotasyonu, proxy, challenge çözme YOK).

Kullanım:
  python -m scripts.sample_listings --ilce istanbul-kadikoy --max 200
  python -m scripts.sample_listings --ilce istanbul-besiktas --max 200 --delay 4
"""
import argparse
import json
import math
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = "https://www.emlakjet.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "konum_ornegi.jsonl")


class Engellendi(Exception):
    """Site otomatik erişimi kısıtladı -> derhal dur."""


def _get(s: requests.Session, url: str, delay: float) -> str:
    r = s.get(url, headers={"User-Agent": UA}, timeout=25)
    body = r.text or ""
    low = body[:3000].lower()
    if r.status_code in (403, 429) or "just a moment" in low or "recaptcha" in low:
        raise Engellendi("%s -> HTTP %s" % (url, r.status_code))
    r.raise_for_status()
    time.sleep(delay)
    return body


def tile_merkez(html: str):
    """İlan haritasının karo bloğundan (lat, lng) + ızgara adımı (m)."""
    tiles = set(re.findall(r'MapServer/tile/(\d+)/(\d+)/(\d+)', html))
    if not tiles:
        return None
    zs = [(int(z), int(r), int(c)) for z, r, c in tiles]
    zm = max(z for z, _, _ in zs)
    sel = [(r, c) for z, r, c in zs if z == zm]
    row = min(r for r, _ in sel) + 1
    col = min(c for _, c in sel) + 1
    n = 2 ** zm
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * row / n))))
    lng = col / n * 360 - 180
    adim = 40075016.686 * math.cos(math.radians(lat)) / n
    return round(lat, 6), round(lng, 6), round(adim)


def _num(s):
    if not s:
        return None
    x = re.sub(r"[^\d]", "", str(s))
    return float(x) if x else None


def parse_ilan(html: str, url: str):
    rec = {"url": url}
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            j = json.loads(m.group(1))
        except Exception:
            continue
        for node in (j.get("@graph") or []) if isinstance(j, dict) else []:
            if node.get("@type") == "Product":
                rec["ad"] = node.get("name")
                off = node.get("offers") or {}
                rec["fiyat"] = _num(off.get("price"))
                adr = node.get("address") or {}
                if adr:
                    rec["mahalle"] = (adr.get("streetAddress") or "").replace(" Mahallesi", "").strip()
                    rec["ilce"] = adr.get("addressLocality")
    # ld+json'da adres yoksa: sayfa başlığı "... İstanbul <İlçe> <Mahalle> Mahallesi ..."
    if not rec.get("mahalle"):
        m = re.search(r'İstanbul\s+([A-ZÇĞİÖŞÜ][^\s]+(?:\s[A-ZÇĞİÖŞÜ][^\s]+)?)\s+'
                      r'([^<>"]{2,40}?)\s+Mahallesi', html)
        if m:
            rec["ilce"] = rec.get("ilce") or m.group(1).strip()
            rec["mahalle"] = m.group(2).strip()
    m = re.search(r'BRÜT\s*([0-9.]+)\s*M²\s*\|\s*NET\s*([0-9.]+)\s*M²', html, re.I)
    if m:
        rec["brut_m2"], rec["net_m2"] = _num(m.group(1)), _num(m.group(2))
    else:
        mm = re.findall(r'>\s*([0-9]{2,4})\s*m²\s*<', html)
        if mm:
            v = sorted({float(x) for x in mm})
            rec["brut_m2"] = v[-1]
            rec["net_m2"] = v[0] if len(v) > 1 else None
    mo = re.search(r'>\s*(\d\+\d)\s*<', html)
    if mo:
        rec["oda"] = mo.group(1)
    my = re.search(r'Bina\s*Ya[şs][ıi][^0-9]{0,60}?(\d+)', html, re.I)
    if my:
        rec["bina_yasi"] = int(my.group(1))
    t = tile_merkez(html)
    if t:
        rec["lat"], rec["lng"], rec["izgara_m"] = t
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ilce", required=True, help="örn: istanbul-kadikoy")
    ap.add_argument("--max", type=int, default=150)
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--sayfa", type=int, default=6, help="kaç gezinme sayfası")
    args = ap.parse_args()

    s = requests.Session()
    seen = set()
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            for line in f:
                try:
                    seen.add(json.loads(line).get("url"))
                except Exception:
                    pass

    # MAHALLE BAZLI gezinme: ilçe sayfası mahalle YOLLARINI listeliyor
    # (/satilik-konut/istanbul-kadikoy-caferaga-mahallesi). Mahalle içi
    # varyasyonu ölçmek için ilçe genelinde değil MAHALLE İÇİNDE derinlik
    # gerekiyor. Not: robots.txt'te yasak olan `?mahalle` QUERY parametresidir;
    # bu YOL tabanlı sayfalar (ve `?sayfa=` sayfalaması) yasak listesinde yok.
    links = []
    try:
        html = _get(s, f"{BASE}/satilik-konut/{args.ilce}", args.delay)
        mahalleler = list(dict.fromkeys(
            re.findall(r'/satilik-konut/' + re.escape(args.ilce) + r'-[a-z0-9-]+-mahallesi', html)))
        print("  %d mahalle bulundu" % len(mahalleler), flush=True)
        found = [x for x in dict.fromkeys(re.findall(r'/ilan/[a-z0-9-]+', html))
                 if BASE + x not in seen]
        links += found
        for mp in mahalleler:
            if len(links) >= args.max:
                break
            for p in range(1, args.sayfa + 1):
                u = BASE + mp + (f"?sayfa={p}" if p > 1 else "")
                try:
                    h = _get(s, u, args.delay)
                except Engellendi:
                    raise
                except Exception:
                    break
                new = [x for x in dict.fromkeys(re.findall(r'/ilan/[a-z0-9-]+', h))
                       if BASE + x not in seen and x not in links]
                links += new
                if len(new) < 5:      # sayfa boşaldı -> sonraki mahalle
                    break
                if len(links) >= args.max:
                    break
            print("  %-46s toplam %d ilan" % (mp.split('/')[-1][:46], len(links)), flush=True)
    except Engellendi as e:
        print("[DURDURULDU] site erişimi kısıtladı: %s" % e)
        return
    except Exception as e:
        print("[gezinme hatası] %s" % str(e)[:100])

    links = links[:args.max]
    n = 0
    try:
        with open(OUT, "a", encoding="utf-8") as f:
            for i, path in enumerate(links, 1):
                url = BASE + path
                try:
                    rec = parse_ilan(_get(s, url, args.delay), url)
                except Engellendi as e:
                    print("[DURDURULDU] %s" % e)
                    break
                except Exception:
                    continue
                if rec.get("lat") and rec.get("fiyat") and (rec.get("net_m2") or rec.get("brut_m2")):
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    n += 1
                if i % 20 == 0:
                    print("  %d/%d işlendi, %d kayıt" % (i, len(links), n), flush=True)
    finally:
        print("\nBitti. %d koordinatlı ilan -> %s" % (n, OUT))


if __name__ == "__main__":
    main()
