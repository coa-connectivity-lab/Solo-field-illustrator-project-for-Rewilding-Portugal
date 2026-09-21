"""
acquire_reserves_and_hunting_zones.py
────────────────────────────────────────
Land-tenure context missing from both this repo and data-management: private
reserves and game farms within the 30km study area. Pulled fresh from
official online sources, not folded into the resistance surfaces — their
effect on connectivity (asset vs. barrier) depends on management regime this
project has no first-hand knowledge of, so they're kept as a clearly-labelled
standalone layer instead (see plan, "Land tenure context").

Sources:
  - Faia Brava private nature reserve (Greater Côa Valley, Rewilding Portugal /
    Rewilding Europe-associated) — boundary via OSM relation 16062824
    (source: WDPA, legal basis Aviso n.deg 26026/2010), fetched through
    Nominatim's polygon export.
  - ICNF official hunting-zone cadastre ("zonas de caça": ZCM municipal,
    ZCA associative, ZCT touristic/private) — WFS layer BDG:zonas_caca at
    si.icnf.pt, ICNF's own GeoServer (https://geocatalogo.icnf.pt/).
"""

import os

import geopandas as gpd
import requests

import config

OUT_GPKG = config.DATA_PROCESSED / "land_tenure.gpkg"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/lookup"
FAIA_BRAVA_OSM_ID = "R16062824"

ICNF_WFS_URL = "https://si.icnf.pt/wfs/bdg"
ICNF_HUNTING_LAYER = "BDG:zonas_caca"
ICNF_HUNTING_TYPE_LABELS = {
    "ZCM": "Municipal hunting zone",
    "ZCA": "Associative hunting zone",
    "ZCT": "Touristic/private hunting zone",
}


def fetch_faia_brava() -> gpd.GeoDataFrame:
    resp = requests.get(
        NOMINATIM_URL,
        params={"osm_ids": FAIA_BRAVA_OSM_ID, "format": "geojson", "polygon_geojson": 1},
        headers={"User-Agent": "coa-eco-connectivity-research/1.0"},
        timeout=20,
    )
    resp.raise_for_status()
    gdf = gpd.GeoDataFrame.from_features(resp.json()["features"], crs=config.CRS_DISPLAY)
    gdf["name"] = "Faia Brava"
    gdf["tenure_type"] = "private_nature_reserve"
    return gdf[["name", "tenure_type", "geometry"]]


def fetch_hunting_zones(study_area_display: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = study_area_display.total_bounds
    resp = requests.get(
        ICNF_WFS_URL,
        params={
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": ICNF_HUNTING_LAYER,
            "outputFormat": "application/json",
            "bbox": f"{minx},{miny},{maxx},{maxy},EPSG:4326",
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    # The WFS ignores the requested bbox CRS and always returns EPSG:3763
    # (ETRS89 / Portugal TM06) coordinates - confirmed from the response's
    # own "crs" property, not from the request we sent.
    source_crs = data.get("crs", {}).get("properties", {}).get("name", "EPSG:3763")
    gdf = gpd.GeoDataFrame.from_features(data["features"], crs=source_crs)
    gdf["tenure_type"] = gdf["fig_ord"].map(ICNF_HUNTING_TYPE_LABELS).fillna(gdf["fig_ord"])
    gdf = gdf.rename(columns={"desig_fig": "name"})
    return gdf[["name", "fig_ord", "tenure_type", "geometry"]]


def main() -> None:
    # Reuse the shipped layer (collaborators' data bundle) unless a refresh is asked for.
    # To re-download from Nominatim/ICNF (needs internet): REFRESH_LAND_TENURE=1
    if OUT_GPKG.exists() and not os.environ.get("REFRESH_LAND_TENURE"):
        print(f"Using existing {OUT_GPKG.name} (set REFRESH_LAND_TENURE=1 to re-download)")
        return

    study_area = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="study_area")
    study_area_display = study_area.to_crs(config.CRS_DISPLAY)

    faia_brava = fetch_faia_brava()
    faia_brava_metric = faia_brava.to_crs(config.CRS_METRIC)
    faia_brava_clipped = gpd.clip(faia_brava_metric, study_area)
    faia_brava_clipped.to_file(OUT_GPKG, layer="private_reserves", driver="GPKG")
    print(f"Private reserves: {len(faia_brava_clipped)} (Faia Brava)")

    hunting = fetch_hunting_zones(study_area_display)
    hunting_metric = hunting.to_crs(config.CRS_METRIC)
    hunting_clipped = gpd.clip(hunting_metric, study_area)
    hunting_clipped.to_file(OUT_GPKG, layer="hunting_zones", driver="GPKG")
    print(f"Hunting zones (ICNF zonas de caça): {len(hunting_clipped)}")
    print(hunting_clipped["fig_ord"].value_counts().to_string())

    print(f"Wrote {OUT_GPKG}")


if __name__ == "__main__":
    main()
