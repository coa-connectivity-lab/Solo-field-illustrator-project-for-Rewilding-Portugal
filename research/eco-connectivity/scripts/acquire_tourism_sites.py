"""
acquire_tourism_sites.py
──────────────────────────
Two point layers for the QGIS map only (not used in the notebook's raster
pipeline): sites named in field-trip notes as upcoming/not-yet-visited
(geocoded via Nominatim, or taken from this project's own recorded test
coordinates where already available), and the known visitor/interpretive
sites already used as the eco-tourism access-value anchor in
build_tradeoff_maps.py, here cross-referenced against the combined
connectivity raster so each site's actual corridor impact is visible on
the map rather than assumed.
"""

import geopandas as gpd
import numpy as np
import rioxarray
import xarray as xr

import config
from build_tradeoff_maps import VISITOR_SITES_WGS84

OUT_GPKG = config.DATA_PROCESSED / "tourism_sites.gpkg"

# Named in field-trips/*.md and field-notes/*.md as upcoming reconnaissance
# (dated after this project's "today", 2026-08-19) - not yet visited as of
# this analysis. Vale Carapito coordinates are this project's own recorded
# test point (survey123/dummy-data.md); the others are geocoded (Nominatim).
NOT_YET_VISITED_WGS84 = [
    ("Vale Carapito (Movement chapter, rewilding site)", 40.6562341, -6.9092832),
    ("Ponte de Sequeiros", 40.4771839, -7.0025485),
    ("Ribeira do Mosteiro / Sernancelhe area (Connection chapter)", 40.9174489, -7.5119079),
]


def main() -> None:
    not_visited = gpd.GeoDataFrame(
        {"name": [s[0] for s in NOT_YET_VISITED_WGS84]},
        geometry=gpd.points_from_xy(
            [s[2] for s in NOT_YET_VISITED_WGS84], [s[1] for s in NOT_YET_VISITED_WGS84]
        ),
        crs=config.CRS_DISPLAY,
    ).to_crs(config.CRS_METRIC)
    not_visited.to_file(OUT_GPKG, layer="not_yet_visited", driver="GPKG")
    print(f"not_yet_visited: {len(not_visited)} sites")

    sites = gpd.GeoDataFrame(
        {"name": [s[0] for s in VISITOR_SITES_WGS84]},
        geometry=gpd.points_from_xy(
            [s[2] for s in VISITOR_SITES_WGS84], [s[1] for s in VISITOR_SITES_WGS84]
        ),
        crs=config.CRS_DISPLAY,
    ).to_crs(config.CRS_METRIC)

    conn = rioxarray.open_rasterio(
        config.OUTPUT_RASTERS / "multispecies_mean_connectivity.tif", masked=True
    ).squeeze("band", drop=True)
    xs = xr.DataArray(sites.geometry.x.values, dims="points")
    ys = xr.DataArray(sites.geometry.y.values, dims="points")
    sampled = conn.sel(x=xs, y=ys, method="nearest").values
    sites["connectivity_value"] = sampled
    sites["corridor_note"] = np.where(
        sampled >= np.nanmedian(conn.values), "high-connectivity zone", "low-connectivity zone"
    )
    sites.to_file(OUT_GPKG, layer="potential_ecotourism_sites", driver="GPKG")
    print(f"potential_ecotourism_sites: {len(sites)} sites")
    print(sites[["name", "connectivity_value", "corridor_note"]].to_string(index=False))
    print(f"Wrote {OUT_GPKG}")


if __name__ == "__main__":
    main()
