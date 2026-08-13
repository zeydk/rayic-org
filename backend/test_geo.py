import requests
import json
import sys

def geocode_arcgis(address: str):
    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
    params = {"singleLine": address, "f": "json", "maxLocations": 1}
    resp = requests.get(url, params=params, timeout=5)
    print(resp.json())

geocode_arcgis(sys.argv[1])
