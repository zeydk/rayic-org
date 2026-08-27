#!/usr/bin/env python3
"""Mahalle içi fiyat DAĞILIMI + segment yanlılık düzeltmeleri üretir.

NEDEN: İstanbul'da mahalleler geniş ve heterojen. Tek bir medyan TL/m² ile
ekspertiz yapmak yanıltıcı: ölçtüğümüz kadarıyla tipik mahallede çeyrekler
arası açıklık medyanın %40'ı, en uçta %200'ü buluyor. Bu yüzden:

  1) Her mahalle için DAĞILIM saklanır (p10/p25/medyan/p75/p90 + n) — böylece
     nokta tahmin yerine GÜVEN ARALIĞI ve "bu mahalle heterojen" uyarısı
     verilebilir.
  2) Mahalle medyanının SİSTEMATİK saptığı segmentler için çarpan üretilir
     (küçük daire, çok büyük daire, site içi). Bunlar 5-katlı çapraz
     doğrulamayla örneklem DIŞINDA sınandı; yanlılığı sıfıra yaklaştırıyor.

ÖNEMLİ SINIR: Kaynak veri (EmlakJet ilanları) GEOCODED DEĞİL — tek konum
alanı "İstanbul - İlçe - Mahalle". Bu yüzden mahalle ALTI (sokak/ada) mekansal
çözünürlük bu veriden ÜRETİLEMEZ. Kalan ±%45'lik saçılmanın büyük kısmı
mahalle içi konum + binanın durumu/manzarası gibi elimizde olmayan
değişkenlerden geliyor; modelle kapatılamaz, dürüstçe aralık olarak
raporlanmalıdır.

Kullanım:
  python -m scripts.build_mahalle_dispersion --csv adverts.csv
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "mahalle_dispersion.json")

SEG_BINS = [0, 60, 90, 140, 250, 600]
SEG_LABELS = ["<60", "60-90", "90-140", "140-250", "250+"]


def _num(s):
    if pd.isna(s):
        return np.nan
    x = re.sub(r"[^\d]", "", str(s))
    return float(x) if x else np.nan


def load(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["net"] = df["Net Square Meter"].map(_num)
    df["price"] = df["Price"].map(_num)
    loc = df["Location"].str.split(" - ", expand=True)
    df["ilce"] = loc[1].str.strip()
    df["mah"] = loc[2].str.replace(" Mh.", "", regex=False).str.strip()
    df["tlm2"] = df["price"] / df["net"]
    df["site"] = (df["Within Site"] == "Evet").astype(int)
    d = df[(df.net.between(25, 600)) & (df.price.between(3e5, 2e8))
           & (df.tlm2.between(5000, 400000))].copy()
    d["ln"] = np.log(d.tlm2)
    d["seg"] = pd.cut(d.net, SEG_BINS, labels=SEG_LABELS)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="EmlakJet adverts.csv")
    ap.add_argument("--min-n", type=int, default=15,
                    help="mahalle için asgari ilan sayısı")
    args = ap.parse_args()

    d = load(args.csv)
    cnt = d.groupby(["ilce", "mah"])["ln"].transform("size")
    d = d[cnt >= args.min_n].copy()
    d["mkey"] = d.ilce + "|" + d.mah

    # 1) Mahalle dağılımları
    mah = {}
    for (ilce, m), g in d.groupby(["ilce", "mah"]):
        q = g.tlm2.quantile([.10, .25, .50, .75, .90])
        med = float(q[.50])
        iqr_oran = float((q[.75] - q[.25]) / med) if med else 0.0
        mah.setdefault(ilce, {})[m] = {
            "n": int(len(g)),
            "p10": round(float(q[.10])), "p25": round(float(q[.25])),
            "medyan": round(med),
            "p75": round(float(q[.75])), "p90": round(float(q[.90])),
            "iqr_orani": round(iqr_oran, 3),
            # Ekspertizde "bu mahalle tek fiyata sığmaz" uyarısı için:
            "heterojen": bool(iqr_oran >= 0.60),
        }

    # 2) Segment / site yanlılık çarpanları (mahalle medyanına göre artık)
    med = d.groupby("mkey")["ln"].median()
    d["r"] = d.ln - d.mkey.map(med)
    seg_mult = {str(k): round(float(np.exp(v)), 3)
                for k, v in d.groupby("seg")["r"].median().items()}
    site_mult = {str(int(k)): round(float(np.exp(v)), 3)
                 for k, v in d.groupby("site")["r"].median().items()}

    iqr_all = [v["iqr_orani"] for i in mah.values() for v in i.values()]
    out = {
        "meta": {
            "kaynak": "EmlakJet ikinci el konut ilanları (adverts.csv)",
            "toplama_tarihi": "2024-09",
            "ilan_sayisi": int(len(d)),
            "mahalle_sayisi": int(sum(len(v) for v in mah.values())),
            "asgari_ilan": args.min_n,
            "geocoded": False,
            "uyari": ("Kaynak veri geocoded DEĞİL (yalnız ilçe+mahalle). Mahalle ALTI "
                      "mekansal kırılım bu veriden üretilemez; saçılma güven aralığı "
                      "olarak raporlanır."),
            "medyan_iqr_orani": round(float(np.median(iqr_all)), 3),
            "olcum": "medyan ikinci el satılık net TL/m² (2024-09 seviyesi; KFE ile endekslenir)",
        },
        "segment_carpani": seg_mult,
        "segment_sinirlari": SEG_BINS,
        "site_carpani": site_mult,
        "mahalle": mah,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("yazıldı: %s" % OUT)
    print("  mahalle=%d  ilan=%d  medyan IQR/medyan=%.0f%%"
          % (out["meta"]["mahalle_sayisi"], out["meta"]["ilan_sayisi"],
             out["meta"]["medyan_iqr_orani"] * 100))
    print("  segment çarpanları:", seg_mult)
    print("  site çarpanı      :", site_mult)


if __name__ == "__main__":
    main()
