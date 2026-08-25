"""
acquire_boundary.py
──────────────────────
Forêt de Fontainebleau boundary - the clip mask for every other layer in
this study.

Source: OSM relation 3236785 (landuse=forest, wikidata=Q1293678, confirmed
matching the Wikidata forest-of-Fontainebleau item's own P402 claim - the
initial concern during planning that P402 was "stale" turned out to be about
Nominatim's lookup endpoint specifically, not the relation itself, which is
real and correctly tagged; confirmed via a geographically-scoped Overpass
query, not the earlier name-only query that had wrongly surfaced Fontainebleau
State Park, Louisiana (OSM relation 18640548, Wikidata Q5465118) as a false
lead - caught before it went into any deliverable).

Fetched via osm_utils.fetch_relation_polygon (Overpass, not osmnx/Nominatim,
which fails for this specific relation - see that module's docstring).

Writes: data/processed/fontainebleau_boundary.gpkg, layer "fontainebleau_boundary"
"""

import geopandas as gpd

import config
from osm_utils import fetch_relation_polygon

FOREST_RELATION_ID = 3236785


def main() -> None:
    geom = fetch_relation_polygon(FOREST_RELATION_ID)
    if geom is None:
        raise RuntimeError(f"Could not assemble a polygon for relation {FOREST_RELATION_ID}")

    gdf = gpd.GeoDataFrame(
        {"name": ["Forêt de Fontainebleau"], "source": [f"OpenStreetMap relation {FOREST_RELATION_ID} (landuse=forest)"]},
        geometry=[geom],
        crs=config.CRS_DISPLAY,
    )

    area_ha = gdf.to_crs(config.CRS_METRIC).geometry.area.sum() / 10_000
    print(f"Forêt de Fontainebleau boundary: {area_ha:,.0f} ha ({area_ha / 100:,.1f} km²)")
    print("Published reference figure: 280.92 km² (Wikidata P2046, forest of Fontainebleau Q1293678) "
          "- compare after running, don't assume a match")
    print(f"Geometry type: {geom.geom_type}, {len(geom.geoms) if hasattr(geom, 'geoms') else 1} parts "
          "(a fragmented boundary is expected - real roads/villages/private inholdings cut through "
          "the nominal forest extent, not a parsing error, see osm_utils.py docstring)")

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    gdf.to_file(config.BOUNDARY_GPKG, layer="fontainebleau_boundary", driver="GPKG")
    print(f"Wrote {config.BOUNDARY_GPKG}")


if __name__ == "__main__":
    main()
