"""
compute_guarda_access.py
──────────────────────────
Real driving distance/time from Guarda to each of the 3 rewilding-site
destinations, via OpenRouteService — same Matrix API pattern as the
livability assignment's acquire_ors_driving_distances.py, plus the actual
Directions route geometry for each leg (needed to draw the routes on the
summary map) and a simple "unpaved-fraction along route" ruggedness
indicator, computed against acquire_offroad_routes.py's own track layer.

Writes:
  ../data/processed/offroad_routes.gpkg, layer "guarda_routes" (3 LineStrings)
  ../output/tables/guarda_access.csv
"""

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, shape

import config


def fetch_matrix() -> dict:
    dest_coords = [[d["lon"], d["lat"]] for d in config.DESTINATIONS]
    locations = [[config.ORIGIN["lon"], config.ORIGIN["lat"]]] + dest_coords
    body = {
        "locations": locations,
        "sources": [0],
        "destinations": list(range(1, len(locations))),
        "metrics": ["distance", "duration"],
    }
    headers = {"Authorization": config.ORS_API_KEY, "Content-Type": "application/json"}
    r = requests.post(config.ORS_MATRIX_URL, json=body, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()


def fetch_route(dest: dict) -> LineString:
    body = {
        "coordinates": [
            [config.ORIGIN["lon"], config.ORIGIN["lat"]],
            [dest["lon"], dest["lat"]],
        ]
    }
    headers = {"Authorization": config.ORS_API_KEY, "Content-Type": "application/json"}
    r = requests.post(config.ORS_DIRECTIONS_URL, json=body, headers=headers, timeout=60)
    r.raise_for_status()
    geojson = r.json()
    geom = shape(geojson["features"][0]["geometry"])
    return geom


def unpaved_fraction(route_line, tracks: gpd.GeoDataFrame, buffer_m: float = 60.0) -> float:
    """Fraction of route length that runs within buffer_m of an acquired
    off-road/unpaved track — a rough proxy for how much of the drive is on
    rugged terrain versus paved road, not a lane-level surface classification."""
    route_metric = gpd.GeoSeries([route_line], crs=config.CRS_DISPLAY).to_crs(config.CRS_METRIC).iloc[0]
    total_len = route_metric.length
    if total_len == 0 or tracks.empty:
        return 0.0
    tracks_union = tracks.to_crs(config.CRS_METRIC).geometry.buffer(buffer_m).union_all()
    overlap = route_metric.intersection(tracks_union)
    return overlap.length / total_len


def main() -> None:
    if not config.ORS_API_KEY:
        raise SystemExit("ORS_API_KEY not found (checked livability assignment's .env) — "
                          "cannot compute real driving distances.")

    matrix = fetch_matrix()
    distances_m = matrix["distances"][0]
    durations_s = matrix["durations"][0]

    tracks = gpd.read_file(config.ROUTES_GPKG, layer="offroad_tracks")

    rows = []
    route_records = []
    for i, dest in enumerate(config.DESTINATIONS):
        route_line = fetch_route(dest)
        frac = unpaved_fraction(route_line, tracks)
        rows.append({
            "origin": config.ORIGIN["name"],
            "destination": dest["name"],
            "drive_distance_km": round(distances_m[i] / 1000, 1),
            "drive_time_min": round(durations_s[i] / 60, 1),
            "unpaved_fraction": round(frac, 3),
        })
        route_records.append({
            "destination": dest["name"],
            "drive_distance_km": round(distances_m[i] / 1000, 1),
            "drive_time_min": round(durations_s[i] / 60, 1),
            "unpaved_fraction": round(frac, 3),
            "geometry": route_line,
        })
        print(f"  {config.ORIGIN['name']} -> {dest['name']}: "
              f"{distances_m[i]/1000:.1f} km, {durations_s[i]/60:.1f} min, "
              f"{frac*100:.1f}% unpaved-adjacent")

    table = pd.DataFrame(rows)
    table.to_csv(config.ACCESS_TABLE_CSV, index=False)
    print(f"\nWrote {config.ACCESS_TABLE_CSV}")

    routes_gdf = gpd.GeoDataFrame(route_records, crs=config.CRS_DISPLAY)
    routes_gdf.to_file(config.ROUTES_GPKG, layer="guarda_routes", driver="GPKG")
    print(f"Wrote {config.ROUTES_GPKG} (layer: guarda_routes)")


if __name__ == "__main__":
    main()
