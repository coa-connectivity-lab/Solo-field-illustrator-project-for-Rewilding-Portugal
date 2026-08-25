"""
acquire_offroad_routes.py
──────────────────────────
Off-road/rugged-terrain track network (OSM highway=track/unclassified,
surface=unpaved/gravel/dirt, tracktype=*) within the Guarda-to-rewilding-
sites routing corridor, via Overpass.

This is the tag set the livability assignment's own MAJOR_ROAD_TAGS
(highway=primary/secondary/trunk/motorway — paved arterial roads only)
explicitly excludes, so this is genuinely new acquisition, not a rerun of
that study's own road layer.

Writes: ../data/processed/offroad_routes.gpkg, layer "offroad_tracks"
"""

import time

import geopandas as gpd
import requests
from shapely.geometry import LineString

import config


def overpass_post(query: str, retries: int = 4, backoff_s: float = 8.0) -> dict:
    """Retry-with-backoff Overpass POST, same pattern as
    research/fontainebleau-comparison/scripts/osm_utils.py::overpass_post()
    (copied rather than cross-imported — see config.py docstring note)."""
    last_exc = None
    for attempt in range(retries):
        try:
            resp = requests.post(
                config.OVERPASS_URL,
                data={"data": query},
                headers={"User-Agent": config.USER_AGENT},
                timeout=90,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as exc:
            last_exc = exc
            wait = backoff_s * (attempt + 1)
            print(f"  Overpass request failed ({exc}), retrying in {wait:.0f}s "
                  f"(attempt {attempt + 1}/{retries})")
            time.sleep(wait)
    raise last_exc


def fetch_offroad_ways() -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = config.ROUTING_BBOX
    bbox = f"{miny},{minx},{maxy},{maxx}"
    # Restricted to highway types a vehicle can legally/physically use
    # (track/unclassified/residential/service) - deliberately excludes
    # highway=path/footway/cycleway/pedestrian even when they carry an
    # unpaved surface tag, since those are foot/bike infrastructure, not a
    # 4x4-relevant network (an unrestricted surface=* query without a
    # highway filter was tried first and pulled in exactly those - checked
    # and rejected before writing this final query).
    vehicle_highways = "track|unclassified|residential|service"
    query = f"""
    [out:json][timeout:120];
    (
      way["highway"="track"]({bbox});
      way["highway"~"^({vehicle_highways})$"]["surface"~"^(unpaved|gravel|dirt|ground|earth)$"]({bbox});
      way["highway"~"^({vehicle_highways})$"]["tracktype"]({bbox});
    );
    out geom;
    """
    data = overpass_post(query)

    rows = []
    for el in data["elements"]:
        if el["type"] != "way" or "geometry" not in el:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
        if len(coords) < 2:
            continue
        tags = el.get("tags", {})
        rows.append({
            "osm_id": el["id"],
            "highway": tags.get("highway"),
            "surface": tags.get("surface"),
            "tracktype": tags.get("tracktype"),
            "geometry": LineString(coords),
        })
    return gpd.GeoDataFrame(rows, crs=config.CRS_DISPLAY)


def main() -> None:
    tracks = fetch_offroad_ways()
    print(f"offroad_tracks: {len(tracks)} ways within routing corridor {config.ROUTING_BBOX}")
    if len(tracks):
        print(tracks["highway"].value_counts(dropna=False).to_string())
        print(tracks["surface"].value_counts(dropna=False).to_string())
        print(tracks["tracktype"].value_counts(dropna=False).to_string())

    tracks_metric = tracks.to_crs(config.CRS_METRIC)
    total_km = tracks_metric.geometry.length.sum() / 1000
    print(f"total off-road track length: {total_km:.1f} km")

    tracks.to_file(config.ROUTES_GPKG, layer="offroad_tracks", driver="GPKG")
    print(f"Wrote {config.ROUTES_GPKG}")


if __name__ == "__main__":
    main()
