"""
acquire_camargue_layers.py
─────────────────────────────
Source data for the Camargue ecotourism comparison map (companion to
field-trips/deskStudy/camargue-ecotourism-implications-coa-valley.md), pulled
fresh from OpenStreetMap — the same source/tooling this project already uses
for Faia Brava's boundary in research/eco-connectivity/scripts/
acquire_reserves_and_hunting_zones.py: Nominatim structured lookup for named
protected-area boundaries, Overpass (via osmnx) for habitat polygons.

This is a standalone comparison study, not part of the Côa Valley
connectivity pipeline — kept in its own folder rather than folded into
research/eco-connectivity, since it covers an unrelated region (southern
France) at a different scale and isn't feeding the resistance/suitability
models there.

Run with the `coa` conda env (geopandas, osmnx, requests all already present
there — nothing new installed for this script).

Writes: ../data/processed/camargue_layers.gpkg
  layers: protected_areas, ecological_zones, ecotourism_facilities

Sources, found by direct Nominatim query on 2026-08-25 (documented here, not
fabricated or guessed):
  - Parc naturel régional de Camargue — OSM relation 5393067
    (boundary=protected_area)
  - Réserve naturelle nationale de Camargue — OSM way 65709366
    (leisure=nature_reserve) — the SNPN-managed 13,232 ha core reserve
    described in the comparison note; OSM's own way geometry may not exactly
    match the official 13,232 ha figure, not reconciled here
  - Habitat polygons (wetland/marsh, salt pans, open water, scrub, beach/dune)
    — Overpass, natural=*/landuse=* tags, queried within the regional park
    boundary. This is a coarse OSM-tag proxy for "ecological regions," not a
    calibrated land-cover classification (no CORINE Land Cover pull was made
    for this pass) — worth flagging plainly rather than presenting it as more
    rigorous than it is.
  - Ecotourism facility points — Nominatim geocoding of named/addressed sites
    from Linda's own 24 May – 17 June 2025 itinerary, plus the park's main
    visitor centre. La Capelière (SNPN's reserve information point,
    referenced in the comparison note) was searched for and returns no
    Nominatim match — left out rather than guessed at; see Open items in the
    comparison note.
"""

from pathlib import Path

import geopandas as gpd
import osmnx as ox
from shapely.geometry import Point

CRS_DISPLAY = "EPSG:4326"   # OSM native, matches this project's config.CRS_DISPLAY
CRS_METRIC = "EPSG:3035"    # ETRS89-LAEA Europe, matches config.CRS_METRIC — valid across France too

OUT_GPKG = Path(__file__).resolve().parent.parent / "data" / "processed" / "camargue_layers.gpkg"

PROTECTED_AREAS = [
    # (osmid string for osmnx.geocode_to_gdf(by_osmid=True), name, designation, year, area_ha)
    ("R5393067", "Parc naturel régional de Camargue", "Regional Nature Park", 1970, 82_000),
    ("W65709366", "Réserve naturelle nationale de Camargue", "National Nature Reserve (SNPN-managed)", 1975, 13_232),
]

# Overpass tags used as a coarse ecological-zone proxy — see module docstring caveat.
HABITAT_TAGS = {
    "natural": ["wetland", "water", "scrub", "beach", "sand", "grassland"],
    "landuse": ["salt_pond", "farmland", "meadow", "vineyard"],
}

# Ecotourism facility points, geocoded via Nominatim on 2026-08-25 (osm_type, osm_id, lat, lon
# recorded for traceability). Not survey123/field-photographed — see the comparison note's
# "no field photography for this trip" flag.
FACILITIES_WGS84 = [
    # name, lat, lon, facility_type, note, source_osm
    ("Office de Tourisme d'Avignon", 43.9449437, 4.8058134, "visitor_information",
     "Gateway regional visitor info point, outside the park itself; first itinerary stop, 24 May 2025",
     "way/83771952"),
    ("Musée de la Camargue (Mas du Pont de Rousty)", 43.6242641, 4.5286227, "visitor_center",
     "The regional park's main interpretive/visitor centre", "way/102094949"),
    ("4x4 safari departure point, 1 Rue Émile Fassin, Arles", 43.6744605, 4.6282490, "tour_operator_departure",
     "Meeting point booked for the 14-15 June 2025 4x4 safari; OSM's own match at this address is a "
     "hotel (Best Western) — most likely the pickup point rather than the safari operator's registered office",
     "node/4239915096"),
    ("Saintes-Maries-de-la-Mer", 43.4515922, 4.4277202, "gateway_town",
     "Main southern gateway town for Camargue tourism — hub for several other 4x4 safari operators, "
     "beach access, and the manade/course camarguaise arena", "relation/414459"),
    ("Étang de Vaccarès", 43.5263231, 4.5686582, "landmark_context",
     "Core lagoon of the national nature reserve; included as an orientation landmark, not a facility",
     "way/787848874"),
    ("Lavender distillery visit, Avenue du Félibrige, Bellegarde", 43.7381654, 4.5214030, "agritourism_site",
     "16-17 June 2025 guided-tour stop (un Mas en Provence); geocoded to the street itself, not the "
     "specific building — no closer Nominatim match found", "way/353944602"),
]


def fetch_protected_areas() -> gpd.GeoDataFrame:
    rows = []
    for osmid, name, designation, year, area_ha in PROTECTED_AREAS:
        gdf = ox.geocode_to_gdf(osmid, by_osmid=True)
        geom = gdf.geometry.iloc[0]
        rows.append({
            "name": name,
            "designation": designation,
            "year_established": year,
            "published_area_ha": area_ha,
            "geometry": geom,
        })
    out = gpd.GeoDataFrame(rows, crs=CRS_DISPLAY)
    return out.to_crs(CRS_METRIC)


def fetch_ecological_zones(park_boundary_wgs84) -> gpd.GeoDataFrame:
    polygon = park_boundary_wgs84.geometry.iloc[0]
    feats = ox.features_from_polygon(polygon, tags=HABITAT_TAGS)
    feats = feats[feats.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
    feats["habitat_type"] = feats.get("natural")
    if "landuse" in feats.columns:
        feats["habitat_type"] = feats["habitat_type"].fillna(feats["landuse"])
    feats = feats[feats["habitat_type"].notna()][["habitat_type", "geometry"]].reset_index(drop=True)
    feats = feats.set_crs(CRS_DISPLAY) if feats.crs is None else feats.to_crs(CRS_DISPLAY)
    return feats.to_crs(CRS_METRIC)


def build_facilities() -> gpd.GeoDataFrame:
    gdf = gpd.GeoDataFrame(
        {
            "name": [f[0] for f in FACILITIES_WGS84],
            "facility_type": [f[3] for f in FACILITIES_WGS84],
            "note": [f[4] for f in FACILITIES_WGS84],
            "source_osm": [f[5] for f in FACILITIES_WGS84],
        },
        geometry=[Point(f[2], f[1]) for f in FACILITIES_WGS84],
        crs=CRS_DISPLAY,
    )
    return gdf.to_crs(CRS_METRIC)


def main() -> None:
    protected = fetch_protected_areas()
    protected.to_file(OUT_GPKG, layer="protected_areas", driver="GPKG")
    print(f"protected_areas: {len(protected)} features")
    print(protected[["name", "designation", "published_area_ha"]].to_string(index=False))

    park_wgs84 = protected[protected["designation"] == "Regional Nature Park"].to_crs(CRS_DISPLAY)
    ecological = fetch_ecological_zones(park_wgs84)
    ecological.to_file(OUT_GPKG, layer="ecological_zones", driver="GPKG")
    print(f"\necological_zones: {len(ecological)} features")
    print(ecological["habitat_type"].value_counts().to_string())

    facilities = build_facilities()
    facilities.to_file(OUT_GPKG, layer="ecotourism_facilities", driver="GPKG")
    print(f"\necotourism_facilities: {len(facilities)} points")
    print(facilities[["name", "facility_type"]].to_string(index=False))

    print(f"\nWrote {OUT_GPKG}")


if __name__ == "__main__":
    main()
