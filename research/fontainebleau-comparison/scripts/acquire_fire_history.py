"""
acquire_fire_history.py
────────────────────────
Fire history for the Forêt de Fontainebleau, new since the report's first
pass. Writes data/processed/fontainebleau_fire_history.gpkg (layer
"fire_history", possibly empty).

Same source and reasoning as research/eco-connectivity/scripts/
acquire_fire_history.py: EFFIS's own historical burnt-area archive needs a
manual data-request form and its live WFS layer errored server-side, so this
uses NASA's MODIS Burned Area Monthly product (MCD64A1.061), real
satellite-derived burn history, served no-auth as Cloud-Optimized GeoTIFFs
via Microsoft Planetary Computer's STAC API. Confirmed reachable and queried
live, 25 August 2026.

Unlike the eco-connectivity pipeline (raster covariates, one grid per
study area), everything else in this Fontainebleau study is vector
(GeoPackages read by generate_maps.py/build_qgis_project.py), so this script
polygonizes the accumulated burn grid into vector features rather than
writing a raster: for every monthly item in [config.FIRE_HISTORY_START,
today], open the Burn_Date band (0=unburned, >0=day-of-year burned,
negative=unmapped/nodata per the MCD64A1 spec), clip to the forest
boundary's bounding box in the item's own native (sinusoidal) grid, and keep
a running "most recent burn year seen so far" per pixel. The final grid is
reprojected to CRS_METRIC, polygonized (only pixels with a recorded burn),
dissolved by year, and clipped to the real forest boundary polygon (not just
its bbox). Reports the true last-available item date rather than assuming
coverage through today - MODIS/Planetary Computer's ingestion lag documented
already in the eco-connectivity script.
"""

import datetime as dt

import geopandas as gpd
import numpy as np
import pystac_client
import planetary_computer
import rioxarray
from rasterio.enums import Resampling
from rasterio.features import shapes
from shapely.geometry import shape

import config


def main() -> None:
    boundary = gpd.read_file(config.BOUNDARY_GPKG, layer="fontainebleau_boundary")
    boundary_wgs84 = boundary.to_crs(config.CRS_DISPLAY)
    bounds_wgs84 = boundary_wgs84.total_bounds

    catalog = pystac_client.Client.open(config.FIRE_STAC_API_URL, modifier=planetary_computer.sign_inplace)
    today = dt.date.today().isoformat()
    search = catalog.search(
        collections=[config.FIRE_STAC_COLLECTION],
        bbox=list(bounds_wgs84),
        datetime=f"{config.FIRE_HISTORY_START}/{today}",
    )
    items = sorted(search.items(), key=lambda it: it.id)
    print(f"Fire history: {len(items)} monthly MODIS items found for {config.FIRE_HISTORY_START} onward")

    empty_schema = gpd.GeoDataFrame(columns=["last_burn_year", "geometry"], geometry="geometry", crs=config.CRS_METRIC)

    if not items:
        print("  No items returned - writing an empty fire-history layer and flagging this plainly.")
        empty_schema.to_file(config.FIRE_GPKG, layer="fire_history", driver="GPKG")
        print(f"Wrote {config.FIRE_GPKG} (0 features)")
        return

    last_burn_year = None
    reference = None
    latest_item_date = None

    for item in items:
        year = int(item.id.split(".")[1][1:5])  # e.g. "A2025182" -> 2025
        latest_item_date = item.id.split(".")[1]
        href = item.assets["Burn_Date"].href
        da = rioxarray.open_rasterio(href).squeeze("band", drop=True)

        boundary_native = boundary_wgs84.to_crs(da.rio.crs)
        try:
            clipped = da.rio.clip_box(*boundary_native.total_bounds)
        except rioxarray.exceptions.NoDataInBounds:
            continue

        if reference is None:
            reference = clipped
            last_burn_year = np.zeros(reference.shape, dtype="int16")
            aligned = clipped
        else:
            aligned = clipped.rio.reproject_match(reference, resampling=Resampling.nearest)

        burned_this_month = aligned.values > 0
        if burned_this_month.any():
            last_burn_year = np.where(burned_this_month, year, last_burn_year)
            print(f"  {item.id}: {burned_this_month.sum()} burned px (year {year})")

    print(f"  Last item processed: {latest_item_date} (this is the true data-currency cutoff, not today)")

    if reference is None or not (last_burn_year > 0).any():
        print("  No burned pixels found in the study window - writing an empty fire-history layer.")
        empty_schema.to_file(config.FIRE_GPKG, layer="fire_history", driver="GPKG")
        print(f"Wrote {config.FIRE_GPKG} (0 features)")
        return

    n_burned_px = int((last_burn_year > 0).sum())
    print(f"Total MODIS pixels (~463 m) with a recorded burn in the window: {n_burned_px}")

    burn_grid = reference.copy(data=last_burn_year)
    burn_grid = burn_grid.rio.reproject(config.CRS_METRIC, resampling=Resampling.nearest)

    records = []
    for geom, value in shapes(burn_grid.values.astype("int32"), transform=burn_grid.rio.transform()):
        if value > 0:
            records.append({"last_burn_year": int(value), "geometry": shape(geom)})

    gdf = gpd.GeoDataFrame(records, crs=config.CRS_METRIC)
    gdf = gdf.dissolve(by="last_burn_year", as_index=False)

    boundary_metric = boundary.to_crs(config.CRS_METRIC)
    gdf = gpd.clip(gdf, boundary_metric)
    gdf = gdf[~gdf.is_empty]

    if gdf.empty:
        print("  Burned pixels found but none intersect the forest boundary polygon itself (bbox-only overlap) - writing an empty fire-history layer.")
        empty_schema.to_file(config.FIRE_GPKG, layer="fire_history", driver="GPKG")
        print(f"Wrote {config.FIRE_GPKG} (0 features)")
        return

    print(f"{len(gdf)} fire-history polygon(s) after dissolve-by-year and clip to the real forest boundary:")
    for _, row in gdf.iterrows():
        print(f"  year {row['last_burn_year']}: {row.geometry.area / 1e4:.2f} ha")

    gdf.to_file(config.FIRE_GPKG, layer="fire_history", driver="GPKG")
    print(f"Wrote {config.FIRE_GPKG} ({len(gdf)} features)")


if __name__ == "__main__":
    main()
