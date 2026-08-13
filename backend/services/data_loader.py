import csv
import os
import math
from typing import Dict, Any

def normalize_string(s: str) -> str:
    if not s:
        return ""
    # Convert turkish chars manually if needed, or just upper
    tr_map = str.maketrans("çğıöşüi", "ÇĞIÖŞÜİ")
    return s.translate(tr_map).upper().strip()

class IbbDamageScenarioLoader:
    def __init__(self):
        self.data = {}
        self._load_data()

    def _load_data(self):
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "ibb_deprem_senaryosu.csv")
        if not os.path.exists(csv_path):
            print(f"Warning: CSV not found at {csv_path}")
            return
            
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                ilce = normalize_string(row.get("ilce_adi", ""))
                mahalle = normalize_string(row.get("mahalle_adi", ""))
                
                try:
                    cok_agir = int(row.get("cok_agir_hasarli_bina_sayisi", 0))
                    agir = int(row.get("agir_hasarli_bina_sayisi", 0))
                    orta = int(row.get("orta_hasarli_bina_sayisi", 0))
                    hafif = int(row.get("hafif_hasarli_bina_sayisi", 0))
                except ValueError:
                    continue
                
                total = cok_agir + agir + orta + hafif
                if total == 0:
                    continue
                    
                key = f"{ilce}_{mahalle}"
                self.data[key] = {
                    "cok_agir_prob": round((cok_agir / total) * 100, 2),
                    "agir_prob": round((agir / total) * 100, 2),
                    "orta_prob": round((orta / total) * 100, 2),
                    "hafif_prob": round((hafif / total) * 100, 2),
                }

    def get_neighborhood_probabilities(self, district: str, neighborhood: str) -> Dict[str, float]:
        d = normalize_string(district)
        n = normalize_string(neighborhood)
        # Fix common abbreviations (e.g., Mah. -> "")
        if n.endswith(" MAH."): n = n[:-5]
        if n.endswith(" MAHALLESİ"): n = n[:-10]
        
        key = f"{d}_{n}"
        if key in self.data:
            return self.data[key]
        
        # Fallback if not found: try partial match
        for k, v in self.data.items():
            if k.startswith(f"{d}_") and (n in k or k.endswith(n)):
                return v
                
        # Ultimate fallback (average values)
        return {
            "cok_agir_prob": 2.5,
            "agir_prob": 7.5,
            "orta_prob": 25.0,
            "hafif_prob": 65.0,
        }

# Singleton instance
ibb_loader = IbbDamageScenarioLoader()
