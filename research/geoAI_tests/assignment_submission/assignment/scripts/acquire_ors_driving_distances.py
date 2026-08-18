"""
Phase 3 (step 4, optional network-distance upgrade): real driving distance
and time from each apartment building to the representative fieldwork
destinations, via the OpenRouteService (ORS) Matrix API.

This replaces the straight-line proxy for the fieldwork_access_score
component with an actual road-network distance, per the assignment's
allowance to add network accessibility "if it can be implemented reliably."
Falls back to straight-line distance (computed elsewhere) if no ORS API
key is configured, so the rest of the pipeline is not blocked by this.

ORS free tier: 500 requests/day, and a matrix call is capped at 50 total
locations (sources + destinations). With 2 fixed destinations, buildings
are batched in groups of 48 sources per request.
"""

import time

import geopandas as gpd
import pandas as pd
import requests

from config import (
    DATA_PROCESSED,
    GEOGRAPHIC_CRS,
    ORS_API_KEY,
    FIELDWORK_DESTINATIONS,
    REWILDING_COMMUNITY_POINTS,
)

# Fetch driving distance/time to every destination we need downstream in one
# pass: the general fieldwork-access site(s) and the rewilding-community
# anchor. Keeping them in one combined request set (rather than two
# separate ORS pulls) is simply more efficient; compute_indicators.py picks
# the right columns for each indicator by destination name, so this does
# not reintroduce the fieldwork/rewilding overlap that was fixed in config.py.
ALL_DESTINATIONS = FIELDWORK_DESTINATIONS + REWILDING_COMMUNITY_POINTS

ORS_MATRIX_URL = "https://api.openrouteservice.org/v2/matrix/driving-car"
BATCH_SIZE = 48  # sources per request, leaving room for 2 destinations (cap: 50 total)
OUT_PATH = DATA_PROCESSED / "ors_driving_distances.csv"


def fetch_batch(building_coords, dest_coords):
    locations = building_coords + dest_coords
    n_sources = len(building_coords)
    n_dest = len(dest_coords)
    body = {
        "locations": locations,
        "sources": list(range(n_sources)),
        "destinations": list(range(n_sources, n_sources + n_dest)),
        "metrics": ["distance", "duration"],
    }
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    r = requests.post(ORS_MATRIX_URL, json=body, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    if not ORS_API_KEY:
        raise SystemExit("ORS_API_KEY not set in assignment/.env -- skipping driving-distance acquisition.")

    buildings = gpd.read_file(DATA_PROCESSED / "apartment_buildings_raw.gpkg", layer="apartment_buildings")
    buildings = buildings.to_crs(GEOGRAPHIC_CRS)
    centroids = buildings.geometry.centroid

    dest_coords = [[d["lon"], d["lat"]] for d in ALL_DESTINATIONS]
    dest_names = [d["name"] for d in ALL_DESTINATIONS]

    rows = []
    n = len(buildings)
    print(f"Requesting driving distances for {n} buildings to {len(dest_coords)} destinations, "
          f"in batches of {BATCH_SIZE}...")

    for start in range(0, n, BATCH_SIZE):
        end = min(start + BATCH_SIZE, n)
        batch_ids = buildings["building_id"].iloc[start:end].tolist()
        batch_coords = [[pt.x, pt.y] for pt in centroids.iloc[start:end]]

        result = fetch_batch(batch_coords, dest_coords)
        distances = result["distances"]  # metres
        durations = result["durations"]  # seconds

        for building_id, dist_row, dur_row in zip(batch_ids, distances, durations):
            row = {"building_id": building_id}
            for i, name in enumerate(dest_names):
                row[f"drive_dist_m__{name}"] = dist_row[i]
                row[f"drive_time_s__{name}"] = dur_row[i]
            rows.append(row)

        print(f"  batch {start}-{end} of {n} done")
        time.sleep(1.5)  # stay well under the free-tier rate limit

    table = pd.DataFrame(rows)
    table.to_csv(OUT_PATH, index=False)

    print(f"\nSaved {len(table)} rows to {OUT_PATH}")
    print(table.describe().to_string())
