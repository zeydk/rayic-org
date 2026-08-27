#!/usr/bin/env python3
"""Mahalle İÇİ konum fiyat çarpanını ÖLÇER (tahmin değil, kestirim).

TASARIM — neden mahalle sabit etkisi:
    log(TL/m²) = mahalle_sabit_etkisi + b·konum + c·daire_ozellikleri + hata

Mahalle sabit etkisi, mahallenin genel fiyat seviyesini soğurur; geriye
YALNIZCA mahalle İÇİ değişim kalır. Yani `b` tam olarak aradığımız şeydir:
"aynı mahallede, aynı nitelikte daire, konumu farklı olsa fiyatı ne değişir?"
Bu sayede mahalle m² ortalaması ileride değişse bile çarpan geçerli kalır
(çarpan GÖRELİdir, mahalle ortalamasında 1.00'dir).

Daire özellikleri (m², yaş, oda) KONTROL olarak girer; girmezse konum
katsayısı daire kalitesini üstlenir (Şenlikköy'de 5 kat fark gördük ama
bunun bir kısmı villa/daire farkı, konum değil).

Konum değişkenleri:
  * kıyıya uzaklık (Boğaz / Marmara)
  * en yakın RAYLI SİSTEM durağına uzaklık (metro + Marmaray + banliyö)
  * mahalle merkezine uzaklık (çeper etkisi)

Veri: scripts/sample_listings.py ile toplanan koordinatlı ilanlar
(462 m ızgara). Ölçüm hatası katsayıyı sıfıra çeker (attenuation), yani
bulunan etki muhtemelen GERÇEĞİN ALT SINIRIDIR.

Kullanım:
  python -m scripts.estimate_location_factor [--min-mahalle 3]
"""
import argparse
import collections
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SAMPLE = os.path.join(D, "konum_ornegi.jsonl")
RAIL = os.path.join(D, "rayli_sistem.json")
OUT = os.path.join(D, "konum_carpani.json")

# GERÇEK kıyı çizgisi (OpenStreetMap natural=coastline, ~80 m ızgaraya
# seyreltilmiş 3580 nokta). Önceden 22 elle seçilmiş nokta kullanılıyordu;
# mesafe hatası katsayıyı sıfıra çekiyordu (Caddebostan sahilini 1.34 km
# içeride ölçüyordu, gerçekte 0.26 km).
COAST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "kiyi_cizgisi.json")
with open(COAST, encoding="utf-8") as _f:
    KIYI = [tuple(p) for p in json.load(_f)]


def km(a, b, c, d):
    return math.hypot((a - c) * 111.0, (b - d) * 111.0 * math.cos(math.radians((a + c) / 2)))


def load():
    rows = []
    with open(SAMPLE, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            m2 = r.get("net_m2") or r.get("brut_m2")
            if not (m2 and r.get("fiyat") and r.get("lat") and r.get("mahalle")):
                continue
            tlm2 = r["fiyat"] / m2
            if not (5000 < tlm2 < 900000 and 25 <= m2 <= 600):
                continue
            r["m2"], r["tlm2"] = m2, tlm2
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-mahalle", type=int, default=3,
                    help="mahallede asgari ilan (sabit etki için)")
    args = ap.parse_args()

    rows = load()
    rail = [(d["lat"], d["lng"]) for d in json.load(open(RAIL, encoding="utf-8"))["duraklar"]]
    print("kullanılabilir ilan: %d | raylı durak: %d" % (len(rows), len(rail)))

    for r in rows:
        r["d_kiyi"] = min(km(r["lat"], r["lng"], *p) for p in KIYI)
        r["d_ray"] = min(km(r["lat"], r["lng"], a, b) for a, b in rail)
    # mahalle merkezi = o mahalledeki ilanların ortalaması
    cen = collections.defaultdict(list)
    for r in rows:
        cen[(r.get("ilce"), r["mahalle"])].append((r["lat"], r["lng"]))
    cen = {k: (sum(a for a, _ in v) / len(v), sum(b for _, b in v) / len(v))
           for k, v in cen.items()}
    for r in rows:
        c = cen[(r.get("ilce"), r["mahalle"])]
        r["d_merkez"] = km(r["lat"], r["lng"], *c)

    cnt = collections.Counter((r.get("ilce"), r["mahalle"]) for r in rows)
    keys = [k for k, v in cnt.items() if v >= args.min_mahalle]
    d = [r for r in rows if (r.get("ilce"), r["mahalle"]) in keys]
    # tanımlayıcı varyasyon: mahalle içinde >=2 farklı ızgara hücresi
    cells = collections.defaultdict(set)
    for r in d:
        cells[(r.get("ilce"), r["mahalle"])].add((round(r["lat"], 4), round(r["lng"], 4)))
    keys = [k for k in keys if len(cells[k]) >= 2]
    d = [r for r in d if (r.get("ilce"), r["mahalle"]) in keys]
    print("model: %d ilan, %d mahalle (mahalle içi >=2 hücre)" % (len(d), len(keys)))
    if len(d) < 120:
        print("\n[!] Örneklem henüz yetersiz. Güvenilir kestirim için ~1000+ ilan "
              "ve 60+ mahalle hedefleyin. scripts/sample_listings.py çalışmaya devam etsin.")
        return

    kidx = {k: i for i, k in enumerate(keys)}
    LOC = ["ln_d_kiyi", "ln_d_ray", "ln_d_merkez"]
    CTL = ["ln_m2", "yas", "oda"]
    for r in d:
        r["ln_d_kiyi"] = math.log1p(r["d_kiyi"])
        r["ln_d_ray"] = math.log1p(r["d_ray"])
        r["ln_d_merkez"] = math.log1p(r["d_merkez"])
        r["ln_m2"] = math.log(r["m2"])
        r["yas"] = float(r.get("bina_yasi") or 0)
        o = r.get("oda") or ""
        r["oda"] = float(o.split("+")[0]) if "+" in o else 3.0

    def build(rs, cols):
        X = np.array([[r[c] for c in cols] for r in rs], dtype=float)
        D_ = np.zeros((len(rs), len(keys)))
        for i, r in enumerate(rs):
            D_[i, kidx[(r.get("ilce"), r["mahalle"])]] = 1.0
        return np.c_[X, D_]

    y = np.log([r["tlm2"] for r in d])
    beta = {}
    res_ctl = None
    for cols, lab, tam in ((CTL, "yalnız daire kontrolleri", False),
                           (LOC + CTL, "konum + kontroller", True)):
        X = build(d, cols)
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        res = y - X @ b
        print("\n%s: R²=%.3f  kalan std=%.3f" % (lab, 1 - res.var() / y.var(), res.std()))
        if not tam:
            res_ctl = res
            continue
        beta = dict(zip(cols, b[:len(cols)]))
        # Konumun EK katkısı: kontrollerden sonra kalan varyansın ne kadarı?
        ek = 1 - res.var() / res_ctl.var()
        print("   -> konumun EK açıklaması: %%%.1f (kontrollerden sonra kalan varyansın)" % (ek * 100))
        for c in cols:
            print("   %-12s %+.4f%s" % (c, beta[c],
                  "   -> mesafe 2x olunca %%%+.0f" % ((2 ** beta[c] - 1) * 100)
                  if c.startswith("ln_d") else ""))
        # Örneklem dışı kontrol: konum GERÇEKTEN yardımcı oluyor mu?
        rng = np.random.default_rng(5)
        idx = rng.permutation(len(d))
        F = np.array_split(idx, 5)
        e_ctl, e_loc = [], []
        for k in range(5):
            te = [d[i] for i in F[k]]
            tr = [d[i] for i in np.concatenate([F[j] for j in range(5) if j != k])]
            ytr = np.log([r["tlm2"] for r in tr])
            yte = np.log([r["tlm2"] for r in te])
            for cc, acc in ((CTL, e_ctl), (LOC + CTL, e_loc)):
                bb, *_ = np.linalg.lstsq(build(tr, cc), ytr, rcond=None)
                acc.append(yte - build(te, cc) @ bb)
        e_ctl = np.concatenate(e_ctl)
        e_loc = np.concatenate(e_loc)
        print("\n   ÖRNEKLEM DIŞI  kontroller MAE=%.4f | +konum MAE=%.4f  (%s)"
              % (np.mean(np.abs(e_ctl)), np.mean(np.abs(e_loc)),
                 "konum İYİLEŞTİRİYOR" if np.mean(np.abs(e_loc)) < np.mean(np.abs(e_ctl))
                 else "konum İYİLEŞTİRMİYOR"))
    out = {
        "meta": {
            "amac": "Mahalle içi konum çarpanı (mahalle ortalaması = 1.00).",
            "yontem": "mahalle sabit etkili log-log regresyon; daire özellikleri kontrol.",
            "ornek_n": len(d), "mahalle_n": len(keys),
            "veri": "EmlakJet koordinatlı ilan örneklemi (462 m ızgara)",
            "uyari": ("Konum 462 m ızgaraya yuvarlı; ölçüm hatası katsayıyı sıfıra çeker, "
                      "bulunan etki gerçeğin ALT SINIRI sayılmalıdır."),
        },
        "katsayilar": {k: round(float(v), 4) for k, v in beta.items()},
        "kiyi_nokta_sayisi": len(KIYI),
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nyazıldı: %s" % OUT)


if __name__ == "__main__":
    main()
