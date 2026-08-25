"""
acquire_protected_areas.py
─────────────────────────────
Protected/conservation-area records for Limpopo Province: a Wikidata bbox
pull for general coverage, plus OSM boundary polygons individually fetched
for the named major parks/reserves so the headline sites (Kruger, Mapungubwe,
Marakele, the user's explicit must-includes, plus others found reachable
during planning) carry real boundary geometry rather than Wikidata's often
point-only coordinates.

No live download of South Africa's official SAPAD/PACA database (DFFE, via
egis.environment.gov.za) was possible: that host returned a connection
failure (curl -> HTTP 000) from this environment, confirmed during planning,
not assumed. Documented as a manual-upgrade path in the report's Limitations
section and in data/raw/README.md - not silently substituted without saying so.

Writes: data/processed/limpopo_protected_areas.gpkg, layer "protected_areas"
"""

from datetime import date

import geopandas as gpd
import osmnx as ox
import pandas as pd
import requests
from shapely.geometry import Point

import config

SPARQL_URL = "https://query.wikidata.org/sparql"
RETRIEVED = date.today().isoformat()

CORE_QUERY = """
SELECT DISTINCT ?item ?itemLabel ?coord WHERE {
  SERVICE wikibase:box {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:cornerWest "Point(%f %f)"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerEast "Point(%f %f)"^^geo:wktLiteral .
  }
  ?item wdt:P31/wdt:P279* wd:Q473972 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
""" % (config.DISCOVERY_BBOX[0], config.DISCOVERY_BBOX[1], config.DISCOVERY_BBOX[2], config.DISCOVERY_BBOX[3])

TYPE_QUERY = """
SELECT DISTINCT ?item ?typeLabel WHERE {
  SERVICE wikibase:box {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:cornerWest "Point(%f %f)"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerEast "Point(%f %f)"^^geo:wktLiteral .
  }
  ?item wdt:P31/wdt:P279* wd:Q473972 .
  ?item wdt:P31 ?type .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
""" % (config.DISCOVERY_BBOX[0], config.DISCOVERY_BBOX[1], config.DISCOVERY_BBOX[2], config.DISCOVERY_BBOX[3])

AREA_QUERY = """
SELECT DISTINCT ?item ?area WHERE {
  SERVICE wikibase:box {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:cornerWest "Point(%f %f)"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerEast "Point(%f %f)"^^geo:wktLiteral .
  }
  ?item wdt:P31/wdt:P279* wd:Q473972 .
  ?item wdt:P2046 ?area .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
""" % (config.DISCOVERY_BBOX[0], config.DISCOVERY_BBOX[1], config.DISCOVERY_BBOX[2], config.DISCOVERY_BBOX[3])

# Named major protected areas fetched individually as real OSM boundary
# polygons (not just Wikidata points) - the user's explicit must-includes
# (Kruger, Mapungubwe, Marakele) plus others confirmed reachable during
# planning. (osm_type_prefix+id, name, designation, connectivity_note)
NAMED_PROTECTED_AREAS = [
    ("R1752987", "Kruger National Park", "National Park",
     "Core of the Great Limpopo Transfrontier Park/GLTFCA (fence-removal network with "
     "Limpopo National Park, Mozambique, and Gonarezhou, Zimbabwe) - documented, see "
     "safari-upscaling-coa-valley-limpopo.md for verified GLTFCA figures. Spans Limpopo "
     "and Mpumalanga provinces; only the Limpopo portion is retained after clipping."),
    ("R2522270", "Mapungubwe National Park", "National Park",
     "Core of the Greater Mapungubwe Transfrontier Conservation Area (GMTFCA) - "
     "documented fence-removal network with Northern Tuli Game Reserve (Botswana) and "
     "Tuli Circle Safari Area (Zimbabwe), at the Limpopo/Shashe river confluence."),
    ("R2608453", "Marakele National Park", "National Park",
     "Waterberg massif core protected area; not part of a documented transfrontier "
     "corridor mechanism in the sources checked for this study - isolated relative to "
     "the GLTFCA/GMTFCA network to its north and east."),
    ("W559509165", "Blouberg Nature Reserve", "Provincial Nature Reserve",
     "Northern Soutpansberg-adjacent highland reserve; potential stepping-stone between "
     "Mapungubwe/GMTFCA and the Soutpansberg range - not a documented corridor, flagged "
     "as an inferred linkage candidate only."),
    ("R2766210", "Nylsvley Nature Reserve", "Provincial Nature Reserve / Ramsar wetland",
     "Nyl River floodplain wetland, well south of the main Limpopo conservation cluster - "
     "geographically isolated from the GLTFCA/GMTFCA network."),
    ("W1228491103", "Musina Nature Reserve (Baobab Forest Reserve)", "Provincial Nature Reserve",
     "Adjacent to Mapungubwe National Park near the Zimbabwe border; plausible stepping-"
     "stone within the broader Mapungubwe/GMTFCA landscape, not itself part of the "
     "documented GMTFCA fence-removal footprint per the sources checked."),
    ("R15650480", "Waterberg Biosphere Reserve", "UNESCO Biosphere Reserve",
     "Designation stacked over the Waterberg massif (including Marakele NP); UNESCO "
     "Man and the Biosphere designation - year/hectares to be confirmed against unesco.org "
     "rather than assumed."),
]


def run_sparql(query: str) -> list[dict]:
    resp = requests.get(
        SPARQL_URL,
        params={"query": query},
        headers={"User-Agent": config.USER_AGENT, "Accept": "application/json"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["results"]["bindings"]


def parse_point(coord_wkt: str) -> Point:
    lon, lat = coord_wkt.replace("Point(", "").replace(")", "").split()
    return Point(float(lon), float(lat))


def main() -> None:
    print("Core protected-area query (bbox, item+coord)...")
    core_rows = run_sparql(CORE_QUERY)
    core = pd.DataFrame([
        {
            "qid": r["item"]["value"].rsplit("/", 1)[-1],
            "name": r["itemLabel"]["value"],
            "geometry": parse_point(r["coord"]["value"]),
        }
        for r in core_rows
    ]).drop_duplicates(subset="qid")
    print(f"  {len(core)} protected-area items with coordinates in the discovery bbox")

    print("Type query...")
    type_rows = run_sparql(TYPE_QUERY)
    type_df = pd.DataFrame([
        {"qid": r["item"]["value"].rsplit("/", 1)[-1], "type": r.get("typeLabel", {}).get("value")}
        for r in type_rows
    ])
    types = (
        type_df.groupby("qid")["type"].apply(lambda s: "; ".join(sorted(set(x for x in s if x))))
        if not type_df.empty else pd.Series(dtype=str)
    )

    print("Area query...")
    area_rows = run_sparql(AREA_QUERY)
    area_df = pd.DataFrame([
        {"qid": r["item"]["value"].rsplit("/", 1)[-1], "area_ha_wikidata": r["area"]["value"]}
        for r in area_rows
    ]).drop_duplicates(subset="qid", keep="first")

    core["designation"] = core["qid"].map(types)
    core = core.merge(area_df, on="qid", how="left")

    gdf = gpd.GeoDataFrame(core, geometry="geometry", crs=config.CRS_DISPLAY)

    boundary = gpd.read_file(config.BOUNDARY_GPKG, layer="limpopo_boundary")
    pre_clip = len(gdf)
    gdf = gpd.clip(gdf, boundary)
    print(f"  {pre_clip} before boundary clip -> {len(gdf)} within Limpopo province")
    gdf["source"] = "Wikidata (query.wikidata.org SPARQL, bbox query)"
    gdf["boundary_type"] = "point (Wikidata P625)"
    gdf["connectivity_note"] = None

    print("\nFetching named major protected areas as real OSM boundary polygons...")
    named_rows = []
    for osmid, name, designation, note in NAMED_PROTECTED_AREAS:
        g = ox.geocode_to_gdf(osmid, by_osmid=True)
        geom = g.geometry.iloc[0]
        named_rows.append({
            "qid": None,
            "name": name,
            "designation": designation,
            "area_ha_wikidata": None,
            "geometry": geom,
            "source": f"OpenStreetMap {osmid}",
            "boundary_type": "polygon (OSM)",
            "connectivity_note": note,
        })
        print(f"  {name} ({osmid}) — polygon fetched")
    named_gdf = gpd.GeoDataFrame(named_rows, geometry="geometry", crs=config.CRS_DISPLAY)
    # Clip Kruger (spans into Mpumalanga) to the Limpopo portion only.
    named_gdf = gpd.clip(named_gdf, boundary)

    gdf = pd.concat([gdf, named_gdf], ignore_index=True)
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=config.CRS_DISPLAY)

    # Dedup: several named sites (Kruger, Mapungubwe, Marakele, Nylsvley, Blouberg,
    # Musina, Waterberg Biosphere Reserve) now have both a Wikidata point record (from
    # the generic bbox pull) and a real OSM polygon record (fetched above). Keep the
    # polygon version - it's the authoritative boundary - and drop the point duplicate
    # rather than double-counting the same protected area twice in the final table.
    # "Waterberg Biosphere" (Wikidata) and "Waterberg Biosphere Reserve" (OSM fetch) are
    # the same real-world site under slightly different labels - normalize both to one
    # dedup key rather than let a naming difference smuggle in a duplicate.
    gdf["_name_key"] = (
        gdf["name"].str.lower().str.strip()
        .str.replace(r"^waterberg biosphere.*$", "waterberg biosphere", regex=True)
    )
    gdf["_is_polygon"] = gdf["boundary_type"] == "polygon (OSM)"
    gdf = gdf.sort_values("_is_polygon", ascending=False).drop_duplicates(subset="_name_key", keep="first")
    gdf = gdf.drop(columns=["_name_key", "_is_polygon"])

    gdf["area_ha_computed"] = gdf.to_crs(config.CRS_METRIC).geometry.area / 10_000
    gdf["retrieved"] = RETRIEVED
    gdf["confidence_note"] = gdf["boundary_type"].apply(
        lambda t: "Real OSM boundary polygon - computed area is a direct measurement"
        if t.startswith("polygon")
        else "Wikidata point coordinate only, no boundary polygon - computed area not meaningful "
             "(a point has zero area); rely on area_ha_wikidata (P2046) if present, else unknown"
    )

    out_cols = ["qid", "name", "designation", "boundary_type", "area_ha_wikidata", "area_ha_computed",
                "connectivity_note", "source", "retrieved", "confidence_note", "geometry"]
    gdf = gdf[out_cols]

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    gdf.to_file(config.PROTECTED_GPKG, layer="protected_areas", driver="GPKG")
    gdf.drop(columns="geometry").to_csv(config.OUTPUT_TABLES / "protected_areas.csv", index=False)
    print(f"\nFinal protected_areas: {len(gdf)} records ({len(named_gdf)} with real OSM polygons)")
    print(gdf[["name", "designation", "boundary_type"]].to_string(index=False))
    print(f"\nWrote {config.PROTECTED_GPKG}")
    print(f"Wrote {config.OUTPUT_TABLES / 'protected_areas.csv'}")


if __name__ == "__main__":
    main()
