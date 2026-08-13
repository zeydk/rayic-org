import re

with open("services/spatial_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# Make sure imports exist
if "import math" not in content:
    content = "import math\nfrom concurrent.futures import ThreadPoolExecutor\n" + content

new_geocode_logic = """
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def geocode_arcgis(address: str):
    try:
        url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
        params = {"singleLine": address, "f": "json", "maxLocations": 1}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                loc = data["candidates"][0]["location"]
                return {"lat": float(loc["y"]), "lng": float(loc["x"]), "source": "arcgis"}
    except Exception:
        pass
    return None

def geocode_nominatim(address: str):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json", "limit": 1}
        headers = {"User-Agent": "rayic-org/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 0:
                return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"]), "source": "nominatim"}
    except Exception:
        pass
    return None

def geocode_photon(address: str):
    try:
        url = "https://photon.komoot.io/api/"
        params = {"q": address, "limit": 1}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if "features" in data and len(data["features"]) > 0:
                coords = data["features"][0]["geometry"]["coordinates"]
                return {"lat": float(coords[1]), "lng": float(coords[0]), "source": "photon"}
    except Exception:
        pass
    return None

def geocode_address_to_latlng(address: str) -> Optional[Dict[str, float]]:
    with ThreadPoolExecutor(max_workers=3) as executor:
        f1 = executor.submit(geocode_arcgis, address)
        f2 = executor.submit(geocode_nominatim, address)
        f3 = executor.submit(geocode_photon, address)
        
        results = []
        for f in [f1, f2, f3]:
            res = f.result()
            if res:
                results.append(res)
                
    if not results:
        return None
        
    if len(results) == 1:
        return results[0]
        
    # Consensus building
    # Find two points that are within 1000 meters of each other
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            dist = haversine_distance(results[i]["lat"], results[i]["lng"], results[j]["lat"], results[j]["lng"])
            if dist < 1000:
                # Average them
                return {
                    "lat": (results[i]["lat"] + results[j]["lat"]) / 2,
                    "lng": (results[i]["lng"] + results[j]["lng"]) / 2,
                    "source": f"consensus({results[i]['source']}+{results[j]['source']})"
                }
                
    # If no consensus, fallback to ArcGIS (if it exists) or first result
    for r in results:
        if r["source"] == "arcgis":
            return r
    return results[0]
"""

# Find and replace the old geocode_address_to_latlng
old_regex = r'def geocode_address_to_latlng.*?return None'
content = re.sub(old_regex, new_geocode_logic, content, flags=re.DOTALL)

with open("services/spatial_service.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated spatial_service.py with consensus logic.")
