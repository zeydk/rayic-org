#!/usr/bin/env python3
"""Mahalle & İlçe Rehberi veri setini üretir (paywall'suz, SEO için).

İLKE: Yalnızca GERÇEK kaynaklardan üretilir. Elde olmayan hiçbir gösterge
uydurulmaz; kaynağı olmayan alan JSON'a hiç yazılmaz.

KAYNAKLAR
  * İBB Deprem Senaryosu (ibb_deprem_senaryosu.csv) — MAHALLE bazında bina
    hasar dağılımı, can kaybı, altyapı hasarı, geçici barınma ihtiyacı.
  * İBB Açık Veri "Nüfus Bilgileri" — İLÇE bazında cinsiyet + 5'er yaş dilimi
    (medyan yaş, çocuk/genç/yaşlı oranı buradan hesaplanır).
  * Ağustos 2026 piyasa raporu (piyasa_rayic.json) — satılık/kiralık TL/m².
  * mahalle_dispersion.json — mahalle içi fiyat saçılması (heterojenlik).
  * rayli_sistem.json + kiyi_cizgisi.json — raylı sisteme ve kıyıya uzaklık.
  * tsunami_methuva.json — MeTHuVA su basma derinliği (kıyı mahalleleri).
  * konum_carpani.json — mahalle merkez koordinatları.

BİLEREK DIŞARIDA BIRAKILANLAR: "güvenlik puanı", "eğitim puanı", "yürünebilirlik"
gibi göstergeler kodda yalnızca 10 mahalle için ELLE yazılmış sabitlerdi
(gerçek ölçüm değil). Rehberde bunlara yer verilmedi; gerçek kaynak bulununca
eklenecek.

Kullanım: python -m scripts.build_mahalle_rehberi
"""
import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUT = os.path.join(D, "mahalle_rehberi.json")

YAS_DILIM = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39",
             "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74",
             "75-79", "80-84", "85-89", "90+"]


def nrm(s):
    s = (s or "").strip().lower()
    for a, b in (("ı", "i"), ("İ", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"),
                 ("ö", "o"), ("ç", "c"), ("â", "a"), ("-", " ")):
        s = s.replace(a, b)
    return " ".join(s.split())


def km(a, b, c, d):
    return math.hypot((a - c) * 111.0, (b - d) * 111.0 * math.cos(math.radians((a + c) / 2)))


def _j(name):
    try:
        with open(os.path.join(D, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def demografi_ilce(xlsx_path):
    """İlçe bazında medyan yaş + yaş yapısı (en güncel yıl)."""
    try:
        import pandas as pd
    except ImportError:
        return {}
    try:
        df = pd.read_excel(xlsx_path)
    except Exception:
        return {}
    df = df[df["Yıl"] == df["Yıl"].max()]
    out = {}
    for _, r in df.iterrows():
        bins = []
        for d in YAS_DILIM:
            n = 0
            for c in ("Erkek ve " + d, "Kadın ve " + d):
                if c in r and not pd.isna(r[c]):
                    n += float(r[c])
            bins.append(n)
        tot = sum(bins)
        if tot <= 0:
            continue
        # medyan yaş: kümülatif %50'nin düştüğü dilimde doğrusal ara değer
        hedef, kum, med = tot / 2.0, 0.0, None
        for i, n in enumerate(bins):
            if kum + n >= hedef:
                alt = i * 5
                med = alt + 5.0 * (hedef - kum) / n if n else alt
                break
            kum += n
        idx = {d: i for i, d in enumerate(YAS_DILIM)}
        cocuk = sum(bins[idx["0-4"]:idx["15-19"]])
        genc = sum(bins[idx["15-19"]:idx["35-39"]])
        yasli = sum(bins[idx["65-69"]:])
        erkek = sum(float(r[c]) for c in df.columns if c.startswith("Erkek ve") and not pd.isna(r[c]))
        out[nrm(r["İlçe"])] = {
            "yil": int(r["Yıl"]),
            "nufus": int(tot),
            "medyan_yas": round(med, 1) if med else None,
            "cocuk_genc_orani_pct": round(100 * cocuk / tot, 1),
            "genc_yetiskin_orani_pct": round(100 * genc / tot, 1),
            "yasli_65_orani_pct": round(100 * yasli / tot, 1),
            "erkek_orani_pct": round(100 * erkek / tot, 1),
            "kaynak": "İBB Açık Veri — Nüfus Bilgileri (ilçe bazında)",
        }
    return out


def deprem_mahalle():
    """İBB deprem senaryosundan mahalle bazında hasar özeti."""
    path = os.path.join(D, "ibb_deprem_senaryosu.csv")
    out = {}
    try:
        with open(path, encoding="iso-8859-9") as f:
            for row in csv.DictReader(f, delimiter=";"):
                il, ma = row.get("ilce_adi"), row.get("mahalle_adi")
                if not il or not ma:
                    continue
                def g(k):
                    try:
                        return int(float(row.get(k) or 0))
                    except Exception:
                        return 0
                ca, ag, orta, haf = (g("cok_agir_hasarli_bina_sayisi"), g("agir_hasarli_bina_sayisi"),
                                     g("orta_hasarli_bina_sayisi"), g("hafif_hasarli_bina_sayisi"))
                tot = ca + ag + orta + haf
                out[(nrm(il), nrm(ma))] = {
                    "cok_agir_hasarli_bina": ca, "agir_hasarli_bina": ag,
                    "orta_hasarli_bina": orta, "hafif_hasarli_bina": haf,
                    "hasarli_bina_toplam": tot,
                    "agir_ustu_bina_orani_pct": round(100 * (ca + ag) / tot, 1) if tot else None,
                    "can_kaybi": g("can_kaybi_sayisi"),
                    "agir_yarali": g("agir_yarali_sayisi"),
                    "gecici_barinma": g("gecici_barinma"),
                    "kaynak": "İBB olası deprem senaryosu (mahalle bazında)",
                }
    except Exception:
        pass
    return out


def main():
    piyasa = (_j("piyasa_rayic.json") or {}).get("rayic", {})
    disp = (_j("mahalle_dispersion.json") or {}).get("mahalle", {})
    kc = _j("konum_carpani.json")
    merkez = kc.get("mahalle_merkezleri") or {}
    ilce_merkez = kc.get("ilce_merkezleri") or {}
    ray = [(p[0], p[1]) for p in (kc.get("rayli_duraklar") or [])]
    kiyi = [tuple(p) for p in (_j("kiyi_cizgisi.json") or [])]
    tsu = _j("tsunami_methuva.json")
    dep = deprem_mahalle()
    demo = demografi_ilce(os.path.join(D, "nufus_bilgileri.xlsx"))

    rehber = {}
    for ilce, mahs in piyasa.items():
        ik = nrm(ilce)
        ilce_rec = {"ad": ilce, "mahalleler": {}}
        if ik in demo:
            ilce_rec["demografi"] = demo[ik]
        for mah, mv in mahs.items():
            rec = {"ad": mah}
            if mv.get("satilik"):
                rec["satilik_tlm2"] = mv["satilik"]
            if mv.get("kiralik"):
                rec["kiralik_tlm2"] = mv["kiralik"]
            if mv.get("satilik") and mv.get("kiralik"):
                rec["amortisman_yil"] = round(mv["satilik"] / (mv["kiralik"] * 12), 1)
            # konum
            cands = merkez.get(nrm(mah))
            if cands:
                ic = ilce_merkez.get(ik)
                p = min(cands, key=lambda q: km(q[0], q[1], ic[0], ic[1])) if (ic and len(cands) > 1) else cands[0]
                rec["lat"], rec["lng"] = p[0], p[1]
                if kiyi:
                    rec["kiyiya_km"] = round(min(km(p[0], p[1], a, b) for a, b in kiyi), 2)
                if ray:
                    rec["rayli_sisteme_km"] = round(min(km(p[0], p[1], a, b) for a, b in ray), 2)
            # fiyat saçılması
            dm = (disp.get(ilce) or {}).get(mah)
            if dm:
                rec["fiyat_dagilimi"] = {"p25": dm["p25"], "medyan": dm["medyan"], "p75": dm["p75"],
                                         "ilan_n": dm["n"], "iqr_orani": dm["iqr_orani"],
                                         "heterojen": dm["heterojen"]}
            # deprem
            d = dep.get((ik, nrm(mah)))
            if d:
                rec["deprem"] = d
            # tsunami
            for tk, tv in (tsu.get("ilceler") or {}).items():
                if nrm(tk) == ik:
                    for mk, mvv in (tv.get("mahalleler") or {}).items():
                        if nrm(mk) == nrm(mah):
                            rec["tsunami"] = mvv
            ilce_rec["mahalleler"][mah] = rec
        rehber[ilce] = ilce_rec

    nm = sum(len(v["mahalleler"]) for v in rehber.values())
    out = {
        "meta": {
            "amac": "Paywall'suz mahalle & ilçe rehberi (SEO).",
            "ilce_sayisi": len(rehber), "mahalle_sayisi": nm,
            "demografi_ilce_sayisi": len(demo),
            "deprem_mahalle_sayisi": len(dep),
            "kaynaklar": [
                "İBB olası deprem senaryosu (mahalle bazında bina hasarı/can kaybı)",
                "İBB Açık Veri — Nüfus Bilgileri (ilçe, cinsiyet + yaş dilimi)",
                "Ağustos 2026 piyasa raporu (satılık/kiralık TL/m²)",
                "OpenStreetMap — raylı sistem durakları, kıyı çizgisi, mahalle merkezleri",
                "MeTHuVA tsunami taşkın çalışması",
            ],
            "not": ("Kaynağı olmayan gösterge (ör. 'güvenlik puanı', 'eğitim puanı') "
                    "bilinçli olarak DAHİL EDİLMEDİ; uydurma değer üretilmiyor."),
        },
        "ilceler": rehber,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print("yazıldı: %s" % OUT)
    print("  %d ilçe, %d mahalle | demografi %d ilçe | deprem %d mahalle"
          % (len(rehber), nm, len(demo), len(dep)))


if __name__ == "__main__":
    main()
