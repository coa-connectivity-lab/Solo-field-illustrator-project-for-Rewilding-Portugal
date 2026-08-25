"""
acquire_ecotourism_facilities.py
────────────────────────────────────
Eco-tourism access/facility points for the Fontainebleau massif: climbing/
bouldering areas (the forest's single most famous recreational feature -
1,115 sport=climbing features found within the discovery bbox, confirming
this is a genuinely dense, mapped climbing landscape, not a handful of named
sites the way the Camargue's safari-departure points were), waymarked-trail
information points, parking, and tourism offices.

The climbing-feature count itself is this study's clearest quantitative
signal for the "extreme recreational visitor pressure on a small footprint"
argument the report makes (see field-trips/deskStudy/
fontainebleau-ecotourism-implications-coa-valley.md) - kept as individual
points rather than pre-aggregated, so the density itself is visible on the
map, not asserted in prose alone.

Writes: data/processed/fontainebleau_ecotourism_facilities.gpkg, layer "facilities"
"""

import geopandas as gpd
from shapely.geometry import Point, Polygon

import config
from osm_utils import overpass_post

QUERY = """
[out:json][timeout:60];
(
  node["sport"="climbing"]({s},{w},{n},{e});
  way["sport"="climbing"]({s},{w},{n},{e});
  node["tourism"="information"]({s},{w},{n},{e});
  node["amenity"="parking"]["name"]({s},{w},{n},{e});
  node["office"="tourism"]({s},{w},{n},{e});
  node["name"~"Maison du Parc",i]({s},{w},{n},{e});
);
out center tags;
""".format(
    s=config.DISCOVERY_BBOX[1], w=config.DISCOVERY_BBOX[0],
    n=config.DISCOVERY_BBOX[3], e=config.DISCOVERY_BBOX[2],
)


def classify(tags: dict) -> str:
    if tags.get("sport") == "climbing":
        return "climbing_area"
    if tags.get("tourism") == "information":
        return "trail_information_point"
    if tags.get("amenity") == "parking":
        return "parking"
    if tags.get("office") == "tourism":
        return "tourism_office"
    if "maison du parc" in (tags.get("name") or "").lower():
        return "visitor_center"
    return "other"


def main() -> None:
    data = overpass_post(QUERY)

    rows = []
    for el in data["elements"]:
        tags = el.get("tags", {})
        facility_type = classify(tags)
        if el["type"] == "node":
            geom = Point(el["lon"], el["lat"])
        elif "center" in el:
            geom = Point(el["center"]["lon"], el["center"]["lat"])
        else:
            continue
        rows.append({
            "name": tags.get("name"),
            "facility_type": facility_type,
            "osm_type": el["type"],
            "osm_id": el["id"],
            "geometry": geom,
        })

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=config.CRS_DISPLAY)
    boundary = gpd.read_file(config.BOUNDARY_GPKG, layer="fontainebleau_boundary")
    # A permissive buffer (2 km) around the forest boundary, not a hard clip: many
    # climbing areas, parking and information points sit just outside the strict
    # forest polygon (trailheads, village-edge parking) while still functionally
    # serving forest access - a hard clip would drop real access infrastructure.
    boundary_buffered = boundary.to_crs(config.CRS_METRIC).buffer(2_000).to_crs(config.CRS_DISPLAY)
    pre_clip = len(gdf)
    clipped = gdf[gdf.geometry.within(boundary_buffered.union_all())]
    print(f"{pre_clip} facility features in the discovery bbox -> {len(clipped)} within 2km of the forest boundary")

    clipped = clipped.copy()
    clipped["source"] = "OpenStreetMap (Overpass)"
    clipped["retrieved"] = "2026-08-25"

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    clipped.to_file(config.FACILITIES_GPKG, layer="facilities", driver="GPKG")
    clipped.drop(columns="geometry").to_csv(config.OUTPUT_TABLES / "ecotourism_facilities.csv", index=False)

    print("\nBy facility type:")
    print(clipped["facility_type"].value_counts().to_string())
    print(f"\nWrote {config.FACILITIES_GPKG}")


if __name__ == "__main__":
    main()
