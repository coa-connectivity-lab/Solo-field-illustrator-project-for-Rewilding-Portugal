"""
acquire_protected_areas.py
─────────────────────────────
Protected-area records for the Fontainebleau massif: the UNESCO Biosphere
Reserve, the associated Parc naturel régional du Gâtinais français, the
Forêt Domaniale des Trois Pignons (a separate, associated state forest), and
the full network of named Réserves Biologiques (ONF's strict-protection
mechanism within French state forests) found inside the discovery bbox.

Réserves Biologiques are the closest analogue in this study to GLTFCA/GMTFCA
in the Limpopo comparison note: a real, named, citable conservation
mechanism, not this study's own spatial inference. A first, narrower search
during planning found only 2 (Gros Fouteau, Baudelut); a second, broader
name-pattern search (name matching "réserve biologique" or "Tillaie", not
scoped to a hardcoded list) found 17 in total, including the historically
significant Réserve biologique intégrale de la Tillaie, one of Europe's
oldest forest reserves (established 1853 under Napoleon III's "séries
artistiques") - found by broadening the search, not assumed present just
because it's famous, and not missed by trusting an earlier, narrower result.

INPN (inpn.mnhn.fr / taxref.mnhn.fr), France's official biodiversity
inventory and the natural authoritative source for Réserves Biologiques,
returned an HTTP 403 Cloudflare bot-check from this environment during
planning - not usable here. OSM + Wikidata is the working source, same as
the rest of this study.

Writes: data/processed/fontainebleau_protected_areas.gpkg, layer "protected_areas"
"""

import geopandas as gpd
import osmnx as ox
from shapely.geometry import Polygon

import config
from osm_utils import fetch_relation_polygon, overpass_post

# Overarching designations, individually verified (not part of the RBI/RBD sweep below).
NAMED_PROTECTED_AREAS = [
    ("R9891093", "Réserve de biosphère de Fontainebleau et du Gâtinais", "UNESCO Biosphere Reserve",
     "The overarching international designation for the massif; co-administered with the "
     "regional park authority, same designation-stacking pattern already documented for the "
     "Camargue in camargue-ecotourism-implications-coa-valley.md."),
    ("R5456737", "Parc naturel régional du Gâtinais français", "Regional Nature Park",
     "The regional park whose territory, together with the state forest, forms the biosphere "
     "reserve's footprint."),
    ("R16615234", "Forêt Domaniale des Trois Pignons", "State Forest (ONF)",
     "A separate, associated state forest within the same massif - a genuinely important "
     "bouldering/climbing area in its own right, tagged source=IGN Forêts Publiques."),
]

RBI_RBD_QUERY = """
[out:json][timeout:40];
(
  way["name"~"éserve biologique",i]({s},{w},{n},{e});
  way["boundary"="protected_area"]["name"~"Tillaie",i]({s},{w},{n},{e});
  relation["name"~"éserve biologique",i]({s},{w},{n},{e});
);
out geom;
""".format(
    s=config.DISCOVERY_BBOX[1], w=config.DISCOVERY_BBOX[0],
    n=config.DISCOVERY_BBOX[3], e=config.DISCOVERY_BBOX[2],
)

RBI_RBD_LABELS = {"1": "Réserve Biologique Intégrale (strict reserve)", "4": "Réserve Biologique Dirigée (managed reserve)"}


def try_osmnx(osmid: str):
    try:
        g = ox.geocode_to_gdf(osmid, by_osmid=True)
        return g.geometry.iloc[0]
    except Exception as exc:
        print(f"    osmnx failed for {osmid} ({exc}) - falling back to direct Overpass fetch")
        return None


def fetch_rbi_rbd_network():
    data = overpass_post(RBI_RBD_QUERY)

    rows = []
    for el in data["elements"]:
        tags = el.get("tags", {})
        name = tags.get("name")
        protect_class = tags.get("protect_class")
        if not name:
            continue
        if el["type"] == "way" and "geometry" in el:
            coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
            if len(coords) < 4:
                continue
            geom = Polygon(coords)
        elif el["type"] == "relation":
            geom = fetch_relation_polygon(el["id"])
        else:
            continue
        if geom is None or not geom.is_valid or geom.area == 0:
            print(f"    skipped {name} ({el['type']} {el['id']}) - geometry did not resolve cleanly")
            continue
        rows.append({
            "name": name,
            "designation": RBI_RBD_LABELS.get(protect_class, f"Réserve Biologique (protect_class {protect_class})"),
            "connectivity_note": "Part of the ONF Réserve Biologique network within the state forest - "
                                  "strict (Intégrale) or managed (Dirigée) protection, no active "
                                  "silviculture in the Intégrale case.",
            "geometry": geom,
            "source": f"OpenStreetMap {el['type']} {el['id']}",
        })
    return rows


def main() -> None:
    rows = []
    for osmid, name, designation, note in NAMED_PROTECTED_AREAS:
        geom = try_osmnx(osmid)
        source_method = "osmnx/Nominatim"
        if geom is None:
            relation_id = int(osmid.lstrip("RW"))
            geom = fetch_relation_polygon(relation_id)
            source_method = "direct Overpass (Nominatim could not resolve this relation)"
        if geom is None:
            print(f"  COULD NOT resolve geometry for {name} ({osmid}) - left out, not guessed")
            continue
        rows.append({
            "name": name,
            "designation": designation,
            "connectivity_note": note,
            "geometry": geom,
            "source": f"OpenStreetMap {osmid} ({source_method})",
        })
        print(f"  {name} ({osmid}) - resolved via {source_method}")

    print("\nRéserve Biologique network sweep (name-pattern search, not a hardcoded list)...")
    rbi_rows = fetch_rbi_rbd_network()
    print(f"  {len(rbi_rows)} Réserves Biologiques found")
    rows.extend(rbi_rows)

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=config.CRS_DISPLAY)
    gdf["area_ha_computed"] = gdf.to_crs(config.CRS_METRIC).geometry.area / 10_000
    gdf["retrieved"] = "2026-08-25"
    gdf["confidence_note"] = ("Real OSM boundary polygon; cross-check against INPN/data.gouv.fr recommended "
                               "(INPN unreachable from this environment, see report Limitations)")

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    gdf.to_file(config.PROTECTED_GPKG, layer="protected_areas", driver="GPKG")
    gdf.drop(columns="geometry").to_csv(config.OUTPUT_TABLES / "protected_areas.csv", index=False)
    print(f"\nFinal protected_areas: {len(gdf)} records")
    print(gdf[["name", "designation", "area_ha_computed"]].to_string(index=False))
    print(f"\nWrote {config.PROTECTED_GPKG}")


if __name__ == "__main__":
    main()
