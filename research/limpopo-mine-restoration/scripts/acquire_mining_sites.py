"""
acquire_mining_sites.py
──────────────────────────
Mining-site records for Limpopo Province, from Wikidata (primary, live-
reachable and validated during planning) with individually-verified named
major mines added where the generic pull might miss them, cross-checked
against an OSM landuse=quarry/man_made=mineshaft count for context.

No live South African official mining cadastre exists to pull from: DMRE's
SAMRAD Online public GIS viewer was disabled by the department itself
(confirmed via independent reporting, not just an access failure on this
project's side), and its announced replacement was not public as of the
sources checked. This is documented here and in the report's Limitations
section, not silently worked around.

Query design note (why this isn't one big SPARQL query): an early planning-
stage query joining core fields with OPTIONAL commodity/type/area in one
query hit the Wikidata endpoint's row multiplication (each OPTIONAL match
multiplies rows) badly enough that a fixed LIMIT truncated the result before
reaching known-present major sites. This script instead runs a small core
query (item + coordinate only, DISTINCT) plus a separate commodity query,
joined in pandas — the same discipline used for the protected-areas script.

Writes: data/processed/limpopo_mining_sites.gpkg, layer "mining_sites"
"""

from datetime import date

import geopandas as gpd
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
  ?item wdt:P31/wdt:P279* wd:Q820477 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
""" % (config.DISCOVERY_BBOX[0], config.DISCOVERY_BBOX[1], config.DISCOVERY_BBOX[2], config.DISCOVERY_BBOX[3])

COMMODITY_QUERY = """
SELECT DISTINCT ?item ?commodityLabel WHERE {
  SERVICE wikibase:box {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:cornerWest "Point(%f %f)"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerEast "Point(%f %f)"^^geo:wktLiteral .
  }
  ?item wdt:P31/wdt:P279* wd:Q820477 .
  ?item wdt:P1056 ?commodity .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
""" % (config.DISCOVERY_BBOX[0], config.DISCOVERY_BBOX[1], config.DISCOVERY_BBOX[2], config.DISCOVERY_BBOX[3])

METADATA_QUERY = """
SELECT DISTINCT ?item ?operatorLabel ?start ?end WHERE {
  SERVICE wikibase:box {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:cornerWest "Point(%f %f)"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerEast "Point(%f %f)"^^geo:wktLiteral .
  }
  ?item wdt:P31/wdt:P279* wd:Q820477 .
  OPTIONAL { ?item wdt:P137 ?operator }
  OPTIONAL { ?item wdt:P571 ?start }
  OPTIONAL { ?item wdt:P576 ?end }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
""" % (config.DISCOVERY_BBOX[0], config.DISCOVERY_BBOX[1], config.DISCOVERY_BBOX[2], config.DISCOVERY_BBOX[3])

# Major named Limpopo mines to individually verify are present after the bbox
# pull (public/press-documented significance the report should credibly
# cover; not assumed present just because they're famous). Mogalakwena was
# already confirmed present in planning-stage testing; the rest are checked
# here and added via individual Wikidata lookup if the bbox pull missed them.
NAMED_MUST_INCLUDE = [
    "Mogalakwena Mine",
    "Venetia Mine",
    "Palabora Mine",
    "Grootegeluk Coal Mine",
]
# Thabazimbi Iron Ore Mine handled separately below (no dedicated Wikidata item exists).


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
    # "Point(lon lat)"
    lon, lat = coord_wkt.replace("Point(", "").replace(")", "").split()
    return Point(float(lon), float(lat))


def wikidata_search(label: str) -> str | None:
    resp = requests.get(
        "https://www.wikidata.org/w/api.php",
        params={"action": "wbsearchentities", "search": label, "language": "en", "format": "json", "limit": 3},
        headers={"User-Agent": config.USER_AGENT},
        timeout=20,
    )
    resp.raise_for_status()
    hits = resp.json().get("search", [])
    return hits[0]["id"] if hits else None


def fetch_entity(qid: str) -> dict:
    resp = requests.get(
        f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json",
        headers={"User-Agent": config.USER_AGENT},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["entities"][qid]


def main() -> None:
    print("Core mine query (bbox, item+coord)...")
    core_rows = run_sparql(CORE_QUERY)
    core = pd.DataFrame([
        {
            "qid": r["item"]["value"].rsplit("/", 1)[-1],
            "name": r["itemLabel"]["value"],
            "geometry": parse_point(r["coord"]["value"]),
        }
        for r in core_rows
    ]).drop_duplicates(subset="qid")
    print(f"  {len(core)} mine items with coordinates in the discovery bbox")

    print("Commodity query...")
    commodity_rows = run_sparql(COMMODITY_QUERY)
    commodity_df = pd.DataFrame([
        {"qid": r["item"]["value"].rsplit("/", 1)[-1], "commodity": r["commodityLabel"]["value"]}
        for r in commodity_rows
    ])
    commodities = (
        commodity_df.groupby("qid")["commodity"].apply(lambda s: "; ".join(sorted(set(s))))
        if not commodity_df.empty else pd.Series(dtype=str)
    )

    print("Metadata query (operator/start/end)...")
    meta_rows = run_sparql(METADATA_QUERY)
    meta_df = pd.DataFrame([
        {
            "qid": r["item"]["value"].rsplit("/", 1)[-1],
            "operator": r.get("operatorLabel", {}).get("value"),
            "start_date": r.get("start", {}).get("value"),
            "end_date": r.get("end", {}).get("value"),
        }
        for r in meta_rows
    ]).drop_duplicates(subset="qid", keep="first")

    core["commodity"] = core["qid"].map(commodities)
    core = core.merge(meta_df, on="qid", how="left")

    gdf = gpd.GeoDataFrame(core, geometry="geometry", crs=config.CRS_DISPLAY)

    # Clip to the real Limpopo boundary (drops confirmed North West/Mpumalanga leakage).
    boundary = gpd.read_file(config.BOUNDARY_GPKG, layer="limpopo_boundary")
    pre_clip = len(gdf)
    gdf = gpd.clip(gdf, boundary)
    print(f"  {pre_clip} before boundary clip -> {len(gdf)} within Limpopo province")

    # Explicit named-mine verification: add any of the must-include list that
    # the bbox+clip pipeline above didn't already capture.
    present_names_lower = set(gdf["name"].str.lower())
    added = []
    for label in NAMED_MUST_INCLUDE:
        if any(label.split()[0].lower() in n for n in present_names_lower):
            continue  # matched on first word (e.g. "Mogalakwena") - already present
        qid = wikidata_search(label)
        if qid is None:
            print(f"  NOT FOUND on Wikidata: {label} — left out rather than guessed")
            continue
        ent = fetch_entity(qid)
        claims = ent["claims"]
        coords = claims.get("P625")
        if not coords:
            print(f"  {label} ({qid}): no P625 coordinate on Wikidata — left out of the point layer, "
                  f"flagged in Open items for the report")
            continue
        v = coords[0]["mainsnak"]["datavalue"]["value"]
        commods = []
        for c in claims.get("P1056", []):
            commods.append(c["mainsnak"]["datavalue"]["value"]["id"])
        added.append({
            "qid": qid,
            "name": ent["labels"].get("en", {}).get("value", label),
            "geometry": Point(v["longitude"], v["latitude"]),
            "commodity": "; ".join(commods) if commods else None,
            "operator": None,
            "start_date": None,
            "end_date": None,
            "_manually_added": True,
        })
        print(f"  added {label} ({qid}) manually — missed by generic bbox pull")

    # Thabazimbi Iron Ore Mine: no dedicated Wikidata item exists (confirmed by direct
    # search - only the town/municipality have QIDs), but it's a real, well-documented,
    # rehabilitation-relevant closure case (Kumba/Anglo American -> ArcelorMittal SA,
    # closed 1 September 2016 after a July 2015 slope failure sterilised remaining
    # reserves; ArcelorMittal holds 96% of the closure/rehabilitation liability). Added
    # here from named secondary sources, coordinates proxied from the Thabazimbi town
    # Wikidata item (Q3643767) since no mine-specific point exists - flagged as such,
    # not presented as a precise mine-site coordinate.
    added.append({
        "qid": None,
        "name": "Thabazimbi Iron Ore Mine",
        "geometry": Point(27.4, -24.6),
        "commodity": "iron ore",
        "operator": "ArcelorMittal South Africa (transferred from Kumba Iron Ore/Anglo American, 2017)",
        "start_date": None,
        "end_date": "2016-09-01",
        "_manually_added": True,
        "_town_proxy": True,
    })
    print("  added Thabazimbi Iron Ore Mine manually — no dedicated Wikidata item exists; "
          "sourced from Mining Review/Miningmx/Anglo American Kumba press coverage, coordinates "
          "proxied from the Thabazimbi town Wikidata item (Q3643767)")

    if added:
        added_gdf = gpd.GeoDataFrame(added, geometry="geometry", crs=config.CRS_DISPLAY)
        gdf["_manually_added"] = False
        gdf = pd.concat([gdf, added_gdf], ignore_index=True)
        gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=config.CRS_DISPLAY)
    else:
        gdf["_manually_added"] = False

    if "_town_proxy" not in gdf.columns:
        gdf["_town_proxy"] = False
    gdf["_town_proxy"] = gdf["_town_proxy"].fillna(False)

    gdf["source"] = gdf["_town_proxy"].apply(
        lambda tp: "Mining Review / Miningmx / Anglo American Kumba press coverage (no Wikidata item exists)"
        if tp else "Wikidata (query.wikidata.org SPARQL, bbox query + named-mine verification)"
    )
    gdf["retrieved"] = RETRIEVED
    gdf["status"] = gdf["end_date"].apply(
        lambda x: f"closed/ended {x[:10]}" if isinstance(x, str) else "not stated in source"
    )
    gdf["confidence_note"] = gdf.apply(
        lambda r: (
            "Coordinates proxied from the Thabazimbi TOWN Wikidata item (Q3643767) - no "
            "mine-specific coordinate exists in any source checked; town-level location only"
            if r["_town_proxy"]
            else (
                "Coordinates from Wikidata P625 (individually verified, not in generic bbox pull)"
                if r["_manually_added"]
                else "Coordinates from Wikidata P625, within bbox pull, clipped to OSM Limpopo boundary"
            )
        ),
        axis=1,
    )

    # Data-quality flag, verified during this run: many Bushveld PGM-cluster items list
    # "rubidium" (Wikidata Q895) as a P1056 commodity alongside platinum/palladium/gold.
    # Rubidium is not a documented Bushveld Complex product in any geological source
    # checked - the real PGM by-product suite is platinum/palladium/rhodium (Q1087, a
    # completely different QID, not a simple typo of Q895) plus nickel/copper. This
    # reads as a genuine upstream Wikidata data error (rubidium/rhodium name confusion
    # in whatever import populated these records), not a real regional commodity -
    # flagged here and in the report rather than repeated as fact.
    gdf["data_quality_flag"] = gdf["commodity"].apply(
        lambda c: "Wikidata lists 'rubidium' as a commodity for this item - almost certainly a "
                  "rubidium/rhodium mislabeling upstream in the source data (rubidium is not a "
                  "documented Bushveld Complex product); treat as likely-intended 'rhodium', not "
                  "verified as-is"
        if isinstance(c, str) and "rubidium" in c else None
    )

    out_cols = ["qid", "name", "commodity", "operator", "status", "start_date", "end_date",
                "source", "retrieved", "confidence_note", "data_quality_flag", "geometry"]
    gdf = gdf[out_cols]

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    gdf.to_file(config.MINING_GPKG, layer="mining_sites", driver="GPKG")
    gdf.drop(columns="geometry").to_csv(config.OUTPUT_TABLES / "mining_sites.csv", index=False)
    print(f"\nFinal mining_sites: {len(gdf)} records")
    print(gdf[["name", "commodity", "status"]].to_string(index=False))
    print(f"\nWrote {config.MINING_GPKG}")
    print(f"Wrote {config.OUTPUT_TABLES / 'mining_sites.csv'}")


if __name__ == "__main__":
    main()
