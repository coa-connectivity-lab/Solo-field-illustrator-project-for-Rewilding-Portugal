"""
Phase 3 (step 3, fallback path): extract the OSM layers that repeatedly
failed against every public Overpass mirror tried (overpass-api.de,
overpass.osm.ch, maps.mail.ru) -- major_roads, parking, amenities,
transport_stops -- from a local Geofabrik bulk extract instead.

Why: nature_areas and coa_river succeeded fine via live Overpass queries
(see acquire_indicator_layers.py) and are left as-is. The remaining
categories consistently either got a bare TCP connection refused or a
504 gateway timeout across three different public mirrors -- a live-API
reliability problem, not a query-correctness one. Pulling the whole
Portugal extract once from Geofabrik and filtering it locally with pyrosm
sidesteps live-API flakiness entirely and is also more reproducible: the
exact input file (with its date) is recorded, rather than depending on
whichever public mirror answers on a given day.

Both routes ultimately serve the same underlying OpenStreetMap data, so
mixing them for different layers does not introduce a source inconsistency
beyond the ordinary temporal gap already documented for any OSM-derived
dataset (see report limitations).
"""

import geopandas as gpd
from pyrosm import OSM

from config import (
    DATA_CACHE,
    DATA_PROCESSED,
    GEOGRAPHIC_CRS,
    METRIC_CRS,
    MAJOR_ROAD_TAGS,
    PARKING_TAGS,
    AMENITY_TAGS,
    TRANSPORT_TAGS,
)

PBF_PATH = DATA_CACHE / "portugal-latest.osm.pbf"
WIDE_BUFFER_M = 10_000
LOCAL_BUFFER_M = 2_000


def buffered_bbox(study_area: gpd.GeoDataFrame, buffer_m: float):
    metric = study_area.to_crs(METRIC_CRS)
    buffered = metric.buffer(buffer_m)
    poly = gpd.GeoSeries(buffered, crs=METRIC_CRS).to_crs(GEOGRAPHIC_CRS).iloc[0]
    return poly, poly.bounds  # (minx, miny, maxx, maxy)


def validate_and_report(name: str, gdf: gpd.GeoDataFrame):
    print(f"\n--- {name} ---")
    print(f"Feature count: {len(gdf)}")
    if len(gdf) == 0:
        print("WARNING: no features returned.")
        return
    print("CRS:", gdf.crs)
    print("Geometry types:", gdf.geometry.type.value_counts().to_dict())
    print("Bounds:", gdf.total_bounds)
    invalid = (~gdf.geometry.is_valid).sum()
    print(f"Invalid geometries: {invalid}")


def extract_layer(osm: OSM, clip_polygon, custom_filter: dict, network_type: str | None = None):
    if network_type:
        gdf = osm.get_network(network_type=network_type)
    else:
        gdf = osm.get_data_by_custom_criteria(custom_filter=custom_filter, filter_type="keep")
    if gdf is None or len(gdf) == 0:
        return gpd.GeoDataFrame(geometry=[], crs=GEOGRAPHIC_CRS)
    gdf = gdf.set_crs(GEOGRAPHIC_CRS, allow_override=True) if gdf.crs is None else gdf.to_crs(GEOGRAPHIC_CRS)
    clipped = gpd.clip(gdf, gpd.GeoSeries([clip_polygon], crs=GEOGRAPHIC_CRS))
    return clipped


if __name__ == "__main__":
    if not PBF_PATH.exists():
        raise SystemExit(f"{PBF_PATH} not found -- download it first (see acquire step in scripts/).")

    study_area = gpd.read_file(DATA_PROCESSED / "study_area.gpkg", layer="study_area")
    wide_polygon, wide_bbox = buffered_bbox(study_area, WIDE_BUFFER_M)
    local_polygon, local_bbox = buffered_bbox(study_area, LOCAL_BUFFER_M)

    print(f"Loading {PBF_PATH} clipped to the wide bounding box...")
    osm_wide = OSM(str(PBF_PATH), bounding_box=list(wide_bbox))
    osm_local = OSM(str(PBF_PATH), bounding_box=list(local_bbox))

    layer_specs = [
        ("major_roads", osm_wide, wide_polygon, {"highway": MAJOR_ROAD_TAGS["highway"]}),
        ("parking", osm_local, local_polygon, {"amenity": [PARKING_TAGS["amenity"]]}),
        ("amenities", osm_local, local_polygon, {**AMENITY_TAGS}),
        ("transport_stops", osm_local, local_polygon,
         {k: (v if isinstance(v, list) else [v]) for k, v in TRANSPORT_TAGS.items()}),
    ]

    for name, osm_obj, polygon, tag_filter in layer_specs:
        out_path = DATA_PROCESSED / f"{name}.gpkg"
        if out_path.exists():
            print(f"\nSkipping '{name}': already exists.")
            continue
        print(f"\nExtracting '{name}' with filter {tag_filter}...")
        gdf = extract_layer(osm_obj, polygon, tag_filter)
        validate_and_report(name, gdf)
        if len(gdf) > 0:
            keep_cols = [c for c in gdf.columns if c not in ("geometry",)][:12] + ["geometry"]
            gdf[keep_cols].to_file(out_path, layer=name, driver="GPKG")
            print(f"Saved to {out_path}")
