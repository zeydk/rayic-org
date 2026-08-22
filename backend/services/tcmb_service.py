import os
import re
import datetime
from typing import Dict, Any, List, Optional

import requests
from pydantic import BaseModel


class TCMBIndexPoint(BaseModel):
    date: str
    istanbul_kfe: float
    turkey_kfe: float
    nominal_change_yoy: float
    real_change_yoy: float


# ---------------------------------------------------------------------------
# Fallback series (labelled as "örnek" / illustrative). Replaced automatically
# with LIVE data when a free TCMB EVDS API key is provided via the environment
# variable TCMB_EVDS_KEY (https://evds2.tcmb.gov.tr → "API Anahtarı").
# ---------------------------------------------------------------------------
TCMB_KFE_DATA: List[Dict[str, Any]] = [
    {"date": "2024-Q1", "istanbul_kfe": 1180.4, "turkey_kfe": 1220.5, "nominal_change_yoy": 52.0, "real_change_yoy": -8.2},
    {"date": "2024-Q2", "istanbul_kfe": 1245.8, "turkey_kfe": 1290.1, "nominal_change_yoy": 45.2, "real_change_yoy": -11.5},
    {"date": "2024-Q3", "istanbul_kfe": 1310.2, "turkey_kfe": 1365.4, "nominal_change_yoy": 38.6, "real_change_yoy": -9.8},
    {"date": "2024-Q4", "istanbul_kfe": 1380.0, "turkey_kfe": 1440.0, "nominal_change_yoy": 33.1, "real_change_yoy": -5.4},
    {"date": "2025-Q1", "istanbul_kfe": 1455.5, "turkey_kfe": 1515.2, "nominal_change_yoy": 31.8, "real_change_yoy": -2.1},
    {"date": "2025-Q2", "istanbul_kfe": 1540.0, "turkey_kfe": 1600.0, "nominal_change_yoy": 32.5, "real_change_yoy": 1.4},
    {"date": "2025-Q3", "istanbul_kfe": 1625.0, "turkey_kfe": 1685.0, "nominal_change_yoy": 34.0, "real_change_yoy": 3.8},
    {"date": "2025-Q4", "istanbul_kfe": 1710.0, "turkey_kfe": 1770.0, "nominal_change_yoy": 35.2, "real_change_yoy": 4.5},
    {"date": "2026-Q1", "istanbul_kfe": 1795.0, "turkey_kfe": 1850.0, "nominal_change_yoy": 36.4, "real_change_yoy": 5.2},
    {"date": "2026-Q2", "istanbul_kfe": 1880.0, "turkey_kfe": 1935.0, "nominal_change_yoy": 37.1, "real_change_yoy": 5.8},
]

# EVDS series codes (Konut Fiyat Endeksi, 2017=100). Overridable via env.
_EVDS_TR = os.environ.get("TCMB_EVDS_TR_SERIES", "TP.KFE.TR1")   # Türkiye geneli
_EVDS_IST = os.environ.get("TCMB_EVDS_IST_SERIES", "TP.KFE.IST01")  # İstanbul

# Simple in-process cache so we hit EVDS at most once per process.
_LIVE_CACHE: Optional[Dict[str, Any]] = None


def _fetch_evds_live() -> Optional[Dict[str, Any]]:
    """Fetch the real KFE series from TCMB EVDS. Returns a summary dict or None."""
    key = os.environ.get("TCMB_EVDS_KEY")
    if not key:
        return None
    try:
        end = datetime.date.today()
        start = end - datetime.timedelta(days=550)
        params = {
            "series": f"{_EVDS_TR}-{_EVDS_IST}",
            "startDate": start.strftime("%d-%m-%Y"),
            "endDate": end.strftime("%d-%m-%Y"),
            "type": "json",
            "aggregationTypes": "avg",
        }
        resp = requests.get(
            "https://evds2.tcmb.gov.tr/service/evds/",
            params=params, headers={"key": key}, timeout=8,
        )
        if resp.status_code != 200:
            return None
        rows = resp.json().get("items", [])
        tr_col = _EVDS_TR.replace(".", "_")
        ist_col = _EVDS_IST.replace(".", "_")
        series = []
        for r in rows:
            tr = r.get(tr_col)
            ist = r.get(ist_col)
            if tr in (None, "", "ND") and ist in (None, "", "ND"):
                continue
            series.append({
                "date": r.get("Tarih", ""),
                "istanbul_kfe": float(ist) if ist not in (None, "", "ND") else None,
                "turkey_kfe": float(tr) if tr not in (None, "", "ND") else None,
            })
        if len(series) < 2:
            return None

        latest = series[-1]
        prior = series[-13] if len(series) >= 13 else series[0]
        nominal_yoy = None
        if latest["turkey_kfe"] and prior["turkey_kfe"]:
            nominal_yoy = round((latest["turkey_kfe"] / prior["turkey_kfe"] - 1) * 100, 1)
        return {
            "source": "TCMB EVDS Konut Fiyat Endeksi (KFE) — CANLI",
            "data_mode": "live",
            "base_year": "2017=100",
            "current_date": latest["date"],
            "latest_istanbul_index": latest["istanbul_kfe"] or latest["turkey_kfe"],
            "latest_turkey_index": latest["turkey_kfe"],
            "nominal_change_yoy": nominal_yoy,
            "real_change_yoy": None,
            "trend_data": series,
            "methodology": "Hedonik İndeks Yöntemi (TCMB EVDS canlı API)",
        }
    except Exception:
        return None


def _period_to_ym(date_str: str) -> Optional[int]:
    """Normalize 'YYYY-Qn', 'YYYY-MM' or 'YYYY-M' to a year*12+month ordinal."""
    s = (date_str or "").strip()
    m = re.match(r"(\d{4})\s*[-/]?\s*Q([1-4])", s, re.IGNORECASE)
    if m:
        y = int(m.group(1)); q = int(m.group(2))
        return y * 12 + {1: 2, 2: 5, 3: 8, 4: 11}[q]
    m = re.match(r"(\d{4})[-/](\d{1,2})", s)
    if m:
        return int(m.group(1)) * 12 + int(m.group(2))
    return None


def get_inflation_factor(from_date: str) -> Dict[str, Any]:
    """KFE-based nominal factor to inflate a `from_date` price to the latest
    available index (İstanbul KFE). Uses live EVDS data when available, else the
    labelled reference series. Returns factor + provenance."""
    summ = get_tcmb_kfe_summary()
    series = summ.get("trend_data", []) or TCMB_KFE_DATA
    target = _period_to_ym(from_date)
    pts = []
    for p in series:
        ym = _period_to_ym(p.get("date", ""))
        idx = p.get("istanbul_kfe") or p.get("turkey_kfe")
        if ym is not None and idx:
            pts.append((ym, float(idx), p.get("date", "")))
    if not pts or target is None:
        return {"factor": 1.0, "from_index": None, "to_index": None,
                "from_date": from_date, "to_date": summ.get("current_date"),
                "data_mode": summ.get("data_mode", "fallback")}
    pts.sort()
    # nearest point to the collection date, and the latest point
    from_ym, from_idx, from_lbl = min(pts, key=lambda x: abs(x[0] - target))
    to_ym, to_idx, to_lbl = pts[-1]
    factor = round(to_idx / from_idx, 3) if from_idx else 1.0
    return {
        "factor": max(1.0, factor),
        "from_index": from_idx, "from_date": from_lbl,
        "to_index": to_idx, "to_date": to_lbl,
        "data_mode": summ.get("data_mode", "fallback"),
    }


def get_tcmb_kfe_summary() -> Dict[str, Any]:
    global _LIVE_CACHE
    if _LIVE_CACHE is None:
        _LIVE_CACHE = _fetch_evds_live() or {}
    if _LIVE_CACHE:
        return _LIVE_CACHE

    latest = TCMB_KFE_DATA[-1]
    return {
        "source": "TCMB EVDS Konut Fiyat Endeksi (KFE)",
        "data_mode": "fallback",
        "data_note": "Örnek seri — canlı TCMB için ortam değişkeni TCMB_EVDS_KEY tanımlayın (ücretsiz).",
        "base_year": "2017=100",
        "current_date": latest["date"],
        "latest_istanbul_index": latest["istanbul_kfe"],
        "latest_turkey_index": latest["turkey_kfe"],
        "nominal_change_yoy": latest["nominal_change_yoy"],
        "real_change_yoy": latest["real_change_yoy"],
        "trend_data": TCMB_KFE_DATA,
        "methodology": "Hedonik İndeks Yöntemi (TCMB Açık Veri Portalı)",
    }
