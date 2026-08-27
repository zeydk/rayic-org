#!/usr/bin/env python3
"""İBB resmî adres ağacını YERELE indirir (ilçe → mahalle → sokak → kapı+koordinat).

NEDEN: Eski akış her sorguda "adres metni → geocoding → koordinat → TKGM →
ilçe belediyesinde aynı adresi bulma" zincirini çalıştırıyordu. Bu hem yavaş
hem de her halkada hata biriktiriyordu (yanlış geocode -> yanlış parsel ->
yanlış imar). Adres ağacı yerelde olursa:

  * geocoding TAMAMEN kalkar (kullanıcı zaten listeden seçiyor),
  * kapının koordinatı diskten anında gelir (0 ağ isteği),
  * dış servis çökse/URL değişse bile sistem çalışmaya devam eder.

ÖLÇEK (ölçüldü): 39 ilçe, 973 mahalle, ~95.000 sokak, ~3,7M kapı.
Kapı listesi sokak başına 1 istek -> ~95k istek. Nazik hızda saatler sürer,
bu yüzden KALDIĞI YERDEN DEVAM EDER ve ilçe başına ayrı dosyaya yazar.

Depolama: data/adres/{ilce_id}.json
    {"ilce": {...}, "mahalleler": {mah_id: {"ad":..., "sokaklar": {
        sok_id: {"ad":..., "kapilar": [{"id":..,"ad":..,"lat":..,"lng":..}]}}}}}

Kullanım:
  python -m scripts.prefetch_address --ilce Kadıköy --delay 0.4
  python -m scripts.prefetch_address --hepsi --delay 0.4
  python -m scripts.prefetch_address --durum
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import address_service as A  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "adres")


def _path(ilce_id) -> str:
    return os.path.join(OUT_DIR, "%s.json" % ilce_id)


def _read(ilce_id):
    try:
        with open(_path(ilce_id), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write(ilce_id, data):
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = _path(ilce_id) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, _path(ilce_id))


def indir_ilce(ilce, delay: float, progress=True) -> dict:
    """Bir ilçenin tüm adres ağacını indirir; kaldığı yerden devam eder."""
    data = _read(ilce["id"]) or {"ilce": ilce, "mahalleler": {}}
    mahs = A.mahalleler(ilce["id"])
    yeni_sokak = yeni_kapi = 0
    for mi, m in enumerate(mahs, 1):
        mkey = str(m["id"])
        mrec = data["mahalleler"].setdefault(mkey, {"ad": m["name"], "sokaklar": {}})
        try:
            sokaklar = A.sokaklar(m["id"])
        except Exception:
            continue
        for s in sokaklar:
            skey = str(s["id"])
            if skey in mrec["sokaklar"]:          # zaten indirilmiş -> atla
                continue
            try:
                kaps = A.kapilar(m["id"], s["id"])
            except Exception:
                continue
            mrec["sokaklar"][skey] = {
                "ad": s["name"],
                "kapilar": [{"id": k["id"], "ad": k["name"],
                             "lat": k.get("lat"), "lng": k.get("lng")}
                            for k in kaps],
            }
            yeni_sokak += 1
            yeni_kapi += len(kaps)
            time.sleep(delay)
            if yeni_sokak % 50 == 0:
                _write(ilce["id"], data)
                if progress:
                    print("    %s: %d sokak, %d kapı"
                          % (ilce["name"], yeni_sokak, yeni_kapi), flush=True)
        if progress:
            print("  [%d/%d] %-22s toplam %d sokak"
                  % (mi, len(mahs), m["name"][:22], len(mrec["sokaklar"])), flush=True)
    _write(ilce["id"], data)
    return {"sokak": yeni_sokak, "kapi": yeni_kapi}


def durum():
    il = A.ilceler()
    print("%-16s %9s %9s %11s" % ("İLÇE", "mahalle", "sokak", "kapı"))
    ts = tk = 0
    for x in il:
        d = _read(x["id"])
        if not d:
            print("%-16s %9s %9s %11s" % (x["name"][:16], "-", "-", "-"))
            continue
        ns = sum(len(m["sokaklar"]) for m in d["mahalleler"].values())
        nk = sum(len(s["kapilar"]) for m in d["mahalleler"].values()
                 for s in m["sokaklar"].values())
        ts += ns
        tk += nk
        print("%-16s %9d %9d %11d" % (x["name"][:16], len(d["mahalleler"]), ns, nk))
    print("-" * 48)
    print("%-16s %9s %9d %11d" % ("TOPLAM", "", ts, tk))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ilce", help="tek ilçe adı")
    ap.add_argument("--hepsi", action="store_true", help="39 ilçenin tamamı")
    ap.add_argument("--durum", action="store_true", help="indirme durumunu göster")
    ap.add_argument("--delay", type=float, default=0.4)
    args = ap.parse_args()

    if args.durum:
        durum()
        return

    il = A.ilceler()
    if not il:
        print("[!] İBB adres servisine ulaşılamadı.")
        return
    if args.ilce:
        hedef = [x for x in il if A.norm_tr(x["name"]) == A.norm_tr(args.ilce)]
        if not hedef:
            print("[!] İlçe bulunamadı: %s" % args.ilce)
            return
    elif args.hepsi:
        hedef = il
    else:
        print("[!] --ilce, --hepsi veya --durum verin.")
        return

    for x in hedef:
        print("════ %s ════" % x["name"], flush=True)
        r = indir_ilce(x, args.delay)
        print("  bitti: +%d sokak, +%d kapı" % (r["sokak"], r["kapi"]), flush=True)
    print("\nTAMAMLANDI")


if __name__ == "__main__":
    main()
