"""
osm_utils.py
────────────
Shared helper for fetching an OSM relation's polygon geometry directly via
Overpass, for relations that osmnx/Nominatim can't resolve.

Why this exists: osmnx.geocode_to_gdf(by_osmid=True) works for boundary=
administrative/protected_area relations (used successfully throughout
research/camargue-comparison/ and research/limpopo-mine-restoration/), but
fails for landuse=forest relations like the Forêt de Fontainebleau itself
(OSM relation 3236785) - confirmed during this study's planning research,
Nominatim returns "0 results" for that specific relation even though it's a
real, well-formed multipolygon relation with 90 member ways. This helper
fetches the relation's member ways with full geometry via Overpass's
`out geom;`, keeps only "outer"-role ways (a few of this relation's members
carry other roles, e.g. "sport", tagging climbing areas bundled into the
same relation - not part of the boundary), and polygonizes them.

The Forêt de Fontainebleau's own boundary resolves to 80 separate polygon
fragments this way (real roads, villages, and private inholdings cut through
the nominal forest boundary - not a parsing error), unioned here into one
MultiPolygon.
"""

import time

import requests
from shapely.geometry import LineString
from shapely.ops import linemerge, polygonize, unary_union

import config


def overpass_post(query: str, retries: int = 4, backoff_s: float = 8.0) -> dict:
    """Overpass's public instance is flaky under repeated calls (504 Gateway
    Timeout observed repeatedly during this study's acquisition runs, not a
    one-off) - retry with backoff rather than fail the whole script on a
    transient server issue."""
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
            print(f"    Overpass request failed ({exc}), retrying in {wait:.0f}s "
                  f"(attempt {attempt + 1}/{retries})")
            time.sleep(wait)
    raise last_exc


def fetch_relation_polygon(relation_id: int):
    """Returns a shapely (Multi)Polygon in EPSG:4326, or None if nothing
    could be assembled (never fabricates a placeholder shape)."""
    query = f"""
    [out:json][timeout:60];
    relation({relation_id});
    (._;>;);
    out geom;
    """
    data = overpass_post(query)

    ways = {e["id"]: e for e in data["elements"] if e["type"] == "way"}
    relations = [e for e in data["elements"] if e["type"] == "relation"]
    if not relations:
        return None
    rel = relations[0]

    outer_lines = []
    for m in rel["members"]:
        if m["type"] != "way" or m.get("role") not in ("outer", ""):
            continue
        way = ways.get(m["ref"])
        if way is None or "geometry" not in way:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in way["geometry"]]
        if len(coords) >= 2:
            outer_lines.append(LineString(coords))

    if not outer_lines:
        return None

    merged = linemerge(outer_lines)
    geoms = [merged] if merged.geom_type == "LineString" else list(merged.geoms)
    polys = list(polygonize(geoms))
    if not polys:
        return None
    return unary_union(polys)
