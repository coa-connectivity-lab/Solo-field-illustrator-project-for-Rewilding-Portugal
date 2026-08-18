"""
Phase 3 (step 3): acquire the OSM layers behind each livability indicator
(nature/recreation, Coa river, major roads, parking, everyday amenities,
public transport). Each layer is fetched, validated, and saved separately.

A buffered version of the study-area polygon is used for the query so that
nearby features just outside the strict boundary are not missed when
computing distances for buildings near the edge (edge effect).
"""

import time

import geopandas as gpd
import osmnx as ox
import pandas as pd

from config import (
    DATA_PROCESSED,
    GEOGRAPHIC_CRS,
    METRIC_CRS,
    NATURE_TAGS,
    RIVER_TAGS,
    MAJOR_ROAD_TAGS,
    PARKING_TAGS,
    AMENITY_TAGS,
    TRANSPORT_TAGS,
)

# Public Overpass mirror times out on complex-polygon queries over a
# ~5500 sq km, many-vertex dissolved municipal boundary. Fixes applied below:
# (1) query by bounding box, which Overpass handles far faster than a
#     high-vertex-count polygon, then clip results to the buffered polygon
#     locally; (2) raise osmnx's request timeout for the wide regional
#     queries; (3) retry with backoff, since this sandbox's outbound
#     connection to overpass-api.de is intermittently refused at the TCP
#     level for reasons outside the script's control (observed to recover
#     within seconds to a couple of minutes).
ox.settings.requests_timeout = 90
# The default overpass-api.de mirror is unreachable from this sandbox as of
# 2026-08-18 (confirmed via direct curl, not just from within osmnx).
# overpass.osm.ch responds but has zero real data coverage for this area
# (confirmed via a direct raw query returning 0 for building=apartments,
# which we know is non-zero) -- likely a near-empty test instance, not a
# genuine problem with our query. maps.mail.ru's mirror is reachable, is
# running a current sync (timestamp_osm_base matches today), and returns
# real counts (1897 apartment ways in the wide bbox), so it is used instead.
ox.settings.overpass_url = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
ox.settings.max_query_area_size = 15_000 * 1_000 * 1_000  # ~15,000 sq km, covers our bbox in one request

WIDE_BUFFER_M = 10_000   # nature, river, major roads: regional-scale features
LOCAL_BUFFER_M = 2_000   # parking, amenities, transport: local, walkable features
MAX_RETRIES = 3
RETRY_BACKOFF_S = [5, 15, 30]


def buffered_query_polygon(study_area: gpd.GeoDataFrame, buffer_m: float):
    metric = study_area.to_crs(METRIC_CRS)
    buffered = metric.buffer(buffer_m)
    return gpd.GeoSeries(buffered, crs=METRIC_CRS).to_crs(GEOGRAPHIC_CRS).iloc[0]


def validate_and_report(name: str, gdf: gpd.GeoDataFrame):
    print(f"\n--- {name} ---", flush=True)
    print(f"Feature count: {len(gdf)}")
    if len(gdf) == 0:
        print("WARNING: no features returned.")
        return
    print("CRS:", gdf.crs)
    print("Geometry types:", gdf.geometry.type.value_counts().to_dict())
    print("Bounds:", gdf.total_bounds)
    invalid = (~gdf.geometry.is_valid).sum()
    print(f"Invalid geometries: {invalid}")


def _fetch_one_key_with_retry(bbox, key, values):
    last_error = None
    for attempt, wait_s in enumerate([0] + RETRY_BACKOFF_S):
        if wait_s:
            print(f"    retrying '{key}' after transient error (attempt {attempt}, waited {wait_s}s)...")
            time.sleep(wait_s)
        try:
            return ox.features_from_bbox(bbox, tags={key: values})
        except ox._errors.InsufficientResponseError:
            return None  # genuinely no data for this tag, not a network problem
        except Exception as exc:  # network/connection errors from the Overpass mirror
            last_error = exc
            continue
    print(f"    WARNING: giving up on tag '{key}' after {MAX_RETRIES} retries: {last_error}")
    return None


def fetch_layer(polygon, tags: dict) -> gpd.GeoDataFrame:
    """Query OSM by the polygon's bounding box (fast), then clip to the
    actual buffered polygon (accurate), one tag key at a time so a single
    slow/large key cannot time out the whole batch."""
    bbox = polygon.bounds  # (minx, miny, maxx, maxy) == osmnx's (left, bottom, right, top)

    frames = []
    for key, values in tags.items():
        gdf = _fetch_one_key_with_retry(bbox, key, values)
        if gdf is not None and len(gdf) > 0:
            frames.append(gdf.reset_index())
        time.sleep(2)  # be polite to the shared public Overpass mirror
    if not frames:
        return gpd.GeoDataFrame(geometry=[], crs=GEOGRAPHIC_CRS)

    combined = gpd.GeoDataFrame(gpd.pd.concat(frames, ignore_index=True), crs=frames[0].crs).to_crs(GEOGRAPHIC_CRS)
    if {"element", "osmid"}.issubset(combined.columns):
        combined = combined.drop_duplicates(subset=["element", "osmid"])
    clipped = gpd.clip(combined, gpd.GeoSeries([polygon], crs=GEOGRAPHIC_CRS))
    return clipped


if __name__ == "__main__":
    study_area = gpd.read_file(DATA_PROCESSED / "study_area.gpkg", layer="study_area")

    wide_polygon = buffered_query_polygon(study_area, WIDE_BUFFER_M)
    local_polygon = buffered_query_polygon(study_area, LOCAL_BUFFER_M)

    layer_specs = [
        ("nature_areas", wide_polygon, NATURE_TAGS, "nature_areas.gpkg"),
        ("coa_river", wide_polygon, RIVER_TAGS, "coa_river.gpkg"),
        ("major_roads", wide_polygon, MAJOR_ROAD_TAGS, "major_roads.gpkg"),
        ("parking", local_polygon, PARKING_TAGS, "parking.gpkg"),
        ("amenities", local_polygon, AMENITY_TAGS, "amenities.gpkg"),
        ("transport_stops", local_polygon, TRANSPORT_TAGS, "transport_stops.gpkg"),
    ]

    for name, polygon, tags, filename in layer_specs:
        out_path = DATA_PROCESSED / filename
        if out_path.exists():
            print(f"\nSkipping '{name}': {out_path} already exists from a previous run.")
            validate_and_report(name, gpd.read_file(out_path, layer=name))
            continue
        print(f"\nFetching '{name}'...")
        gdf = fetch_layer(polygon, tags)

        if name == "coa_river":
            # waterway=river with no name filter returns every river in the
            # wide bbox (Douro, Mondego, Vouga, and many tributaries were
            # observed alongside the Coa) -- keep only segments actually
            # named "Rio Coa" (checked accent-insensitively, since OSM
            # stores it with the c-cedilla).
            import unicodedata

            def _is_coa(value):
                if value is None:
                    return False
                stripped = "".join(
                    c for c in unicodedata.normalize("NFD", str(value)) if unicodedata.category(c) != "Mn"
                )
                return "coa" in stripped.lower()

            before = len(gdf)
            gdf = gdf[gdf.get("name", gdf.get("name:pt", pd.Series(dtype=object))).apply(_is_coa)]
            print(f"  filtered to Rio Coa only: {before} -> {len(gdf)} segments")

        validate_and_report(name, gdf)
        if len(gdf) > 0:
            keep_cols = [c for c in gdf.columns if c != "geometry"][:12] + ["geometry"]
            gdf[keep_cols].to_file(DATA_PROCESSED / filename, layer=name, driver="GPKG")
            print(f"Saved to {DATA_PROCESSED / filename}")
