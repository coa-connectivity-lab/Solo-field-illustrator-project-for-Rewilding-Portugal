"""
acquire_unesco_heritage_zones.py
───────────────────────────────────
UNESCO heritage-conflict layer (v3 addition) — two World Heritage areas whose
protected status makes them poor/unavailable matrix for land connectivity,
regardless of the underlying land-cover suitability: the **Alto Douro Wine
Region** (WHC site 1046, ~24,600 ha terraced vineyards) and the **Prehistoric
Rock Art Sites of the Côa Valley** core protected zone (WHC, inscribed 1998,
inside this project's study area). Writes:
  data/processed/heritage_protection.gpkg
    layers: unesco_alto_douro, coa_rock_art_core

Source search, in the order tried (documented plainly, same honesty
convention as acquire_fire_history.py's EFFIS -> MODIS pivot):

  1. UNESCO's own WHC site pages/maps (whc.unesco.org/en/list/1046/maps/,
     .../866/maps/) and its list-wide KML/KMZ export
     (whc.unesco.org/en/list/kml/) — all return HTTP 403 from a Cloudflare
     bot-check ("Just a moment...") when fetched programmatically in this
     session, confirmed with curl. No usable boundary here.
  2. UNEP-WCMC/IUCN's World Database on Protected Areas (WDPA), via
     protectedplanet.net's search API — confirmed reachable, but returns
     zero results for "Alto Douro" or "Côa". This checks out: WDPA is a
     nature-conservation-area database, and both these WHC properties are
     *cultural* sites, not natural/mixed — protectedplanet.net's own KML
     product is explicitly scoped to natural/mixed WH sites only, so this
     was always a long shot, not a real dead end to be alarmed about.
  3. Portugal's own heritage authority, DGPC (Direção-Geral do Património
     Cultural), publishes exactly this data: an ArcGIS Server REST endpoint
     at geo.patrimoniocultural.gov.pt (HTTPS only — the HTTP host serves an
     "SSL required" adaptor error) exposing
     PatrimonioClassificadoEmViasClassificacao/Atlas_Patrimonio_Servicos,
     whose layer 1 ("PatrimonioImovel") carries official classified-property
     boundary polygons for national monuments, each with a `Classifica` text
     field that names the UNESCO inscription directly where applicable. This
     is a real, authoritative, non-fabricated boundary source — used here:
       - OBJECTID 2114, "Alto Douro Vinhateiro" (Classifica cites "MN -
         monumento nacional / património mundial", spanning the 13
         concelhos of the demarcated region) -> unesco_alto_douro.
       - OBJECTID 3677, "Conjunto dos Sítios Arqueológicos no Vale do Rio
         Côa" (Classifica: "Inscrito na Lista do Património Mundial da
         UNESCO em 5-12-1998") -> coa_rock_art_core. This is the national
         monument's own classified-property boundary (a MultiPolygon
         following the individual rock-art nuclei along the river banks,
         ~569 ha total) — the *core* protected zone, not DGPC's separate,
         larger ZEP (Zona Especial de Proteção / buffer) layer, per the ask.

No caveated fallback (buffer-around-coordinates, hand-digitized polygon) was
needed — step 3 produced a clean, official boundary for both areas on the
first query, sanity-checked below against the published Alto Douro area.
"""

from io import BytesIO

import geopandas as gpd
import requests

import config

OUT_GPKG = config.DATA_PROCESSED / "heritage_protection.gpkg"

DGPC_QUERY_URL = (
    "https://geo.patrimoniocultural.gov.pt/arcgis/rest/services/"
    "PatrimonioClassificadoEmViasClassificacao/Atlas_Patrimonio_Servicos/MapServer/1/query"
)
DGPC_HEADERS = {"User-Agent": "coa-eco-connectivity-research/1.0"}

# (OBJECTID in DGPC's PatrimonioImovel layer, output layer name, expected published
# area in hectares for the sanity check below — None where no independent published
# figure was used to design this pull)
TARGETS = [
    (2114, "unesco_alto_douro", 24_600.0),
    (3677, "coa_rock_art_core", None),
]


def _fetch(object_id: int) -> gpd.GeoDataFrame:
    resp = requests.get(
        DGPC_QUERY_URL,
        params={
            "where": f"OBJECTID={object_id}",
            "outFields": "OBJECTID,NINV,Designacao,Concelho,Categoria,Classifica",
            "returnGeometry": "true",
            "outSR": 3035,  # config.CRS_METRIC's EPSG code
            "f": "geojson",
        },
        headers=DGPC_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    # read_file (via pyogrio/GDAL's GeoJSON driver) tolerates this service's ArcGIS-style
    # ring geometries better than shapely.geometry.shape via GeoDataFrame.from_features,
    # which chokes on a null coordinate in at least one of these two features.
    gdf = gpd.read_file(BytesIO(resp.content))
    if gdf.empty:
        raise RuntimeError(f"DGPC query for OBJECTID={object_id} returned no features")
    if gdf.crs is None:
        gdf = gdf.set_crs(config.CRS_METRIC)
    else:
        gdf = gdf.to_crs(config.CRS_METRIC)
    return gdf


def main() -> None:
    for object_id, layer_name, expected_ha in TARGETS:
        gdf = _fetch(object_id)
        assert gdf.crs == config.CRS_METRIC
        area_ha = gdf.geometry.area.sum() / 10_000
        designacao = gdf["Designacao"].iloc[0]

        gdf.to_file(OUT_GPKG, layer=layer_name, driver="GPKG")

        print(f"{layer_name}: '{designacao}' — {len(gdf)} feature(s), area {area_ha:,.1f} ha")
        if expected_ha is not None:
            pct_diff = abs(area_ha - expected_ha) / expected_ha * 100
            print(f"  vs. published figure {expected_ha:,.0f} ha: {pct_diff:.2f}% difference")

    print(f"Wrote {OUT_GPKG} (layers: {', '.join(t[1] for t in TARGETS)})")


if __name__ == "__main__":
    main()
