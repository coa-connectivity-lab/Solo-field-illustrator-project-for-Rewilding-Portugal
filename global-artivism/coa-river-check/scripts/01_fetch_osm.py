"""Step 1: download the Côa (and the Douro reach it joins) fresh from OpenStreetMap
via the Overpass API, as an independent reference for the river line.

Run from this folder's root:  conda run -n coa python scripts/01_fetch_osm.py
Writes raw/osm_coa_overpass.geojson, raw/osm_douro_overpass.geojson, raw/osm_query.txt
"""
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
URL = "https://overpass-api.de/api/interpreter"
BBOX = "40.2,-7.3,41.2,-6.7"  # south, west, north, east

QUERIES = {
    "coa": f'[out:json][timeout:120];way["waterway"="river"]["name"~"C[oô]a$"]({BBOX});out geom tags;',
    "douro": f'[out:json][timeout:120];way["waterway"="river"]["name"~"Douro"]({BBOX});out geom tags;',
}


MIRRORS = [URL, "https://overpass.kumi.systems/api/interpreter",
           "https://overpass.private.coffee/api/interpreter"]


def fetch(query):
    for url in MIRRORS:  # the main server often returns 504; try mirrors in turn
        try:
            r = requests.post(url, data={"data": query}, timeout=180,
                              headers={"User-Agent": "coa-river-check (research script)"})
            r.raise_for_status()
            break
        except requests.RequestException as e:
            print("failed", url, e)
    else:
        raise RuntimeError("all Overpass mirrors failed")
    print("served by", url)
    rows = []
    for el in r.json()["elements"]:
        coords = [(p["lon"], p["lat"]) for p in el.get("geometry", [])]
        if len(coords) > 1:
            t = el.get("tags", {})
            rows.append({"id": el["id"], "name": t.get("name"), "waterway": t.get("waterway"),
                         "geometry": LineString(coords)})
    return gpd.GeoDataFrame(rows, crs=4326), url


stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
log = [f"Downloaded: {stamp}", ""]
for name, q in QUERIES.items():
    gdf, served = fetch(q)
    gdf.to_file(RAW / f"osm_{name}_overpass.geojson", driver="GeoJSON")
    log += [f"[{name}] {len(gdf)} ways, served by {served}", q, ""]
    print(name, len(gdf), "ways")
(RAW / "osm_query.txt").write_text("\n".join(log))
