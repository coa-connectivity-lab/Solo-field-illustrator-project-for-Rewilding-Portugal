"""
acquire_fire_history.py
─────────────────────────
Fire as a barrier to land restoration — new in v2. Writes:
  data/processed/covariates/fire_last_burn_year.tif

EFFIS's own historical burnt-area archive needs a manual data-request form
(https://effis.jrc.ec.europa.eu/apps/data.request.form), and its live WFS burnt-area
layer errored server-side in this session (Oracle Spatial connection failure on their
end) — neither is usable for automated acquisition. Confirmed with Linda: use NASA's
MODIS Burned Area Monthly product (MCD64A1.061) instead — real satellite-derived burn
history, served as public, no-auth Cloud-Optimized GeoTIFFs via Microsoft Planetary
Computer's STAC API (config.FIRE_STAC_API_URL/FIRE_STAC_COLLECTION).

Data-currency limitation, found this session and stated plainly rather than papered
over: Planetary Computer's ingestion of this collection currently tops out at day
182/2025 (~1 July 2025) *globally*, not just for this tile — checked directly. That
means it cannot capture the Rewilding Portugal annual review's 2025 summer fires (if
they landed after that date) or the field-note-documented July 2026 wildfire near
Almeida/Sabugal/Pinhel. Those stay narrative-only in the notebook; this script uses
whatever the catalog actually has, and reports the true last-available date rather than
assuming full coverage through config.FIRE_HISTORY_END.

Method: for every monthly item in [config.FIRE_HISTORY_START, today], open the
Burn_Date band (0=unburned, >0=day-of-year burned, negative=unmapped/nodata per the
MCD64A1 spec), clip to the study area's native-CRS bounding box, reproject onto the
already-clipped elevation.tif grid (nearest resampling — this is a categorical "which
year did this burn" value, not something to interpolate), and keep a running
"most recent burn year seen so far" per pixel. No vector burnt-area polygons are
produced — every other covariate in this pipeline is raster-only, and a vector layer
here would just be more unused context (see hydrology_and_protected_areas.gpkg's
water_bodies layer, which is never consumed anywhere).
"""

import datetime as dt

import geopandas as gpd
import numpy as np
import pystac_client
import planetary_computer
import rioxarray
from rasterio.enums import Resampling

import config

REFERENCE_RASTER = config.DATA_PROCESSED / "covariates" / "elevation.tif"
OUT_RASTER = config.DATA_PROCESSED / "covariates" / "fire_last_burn_year.tif"


def main() -> None:
    if not REFERENCE_RASTER.exists():
        raise FileNotFoundError(
            f"{REFERENCE_RASTER} not found — run acquire_environmental_covariates.py "
            "(against the extended study area) before this script."
        )

    study_area = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="study_area")
    bounds_wgs84 = study_area.to_crs(config.CRS_DISPLAY).total_bounds
    reference = rioxarray.open_rasterio(REFERENCE_RASTER).squeeze("band", drop=True)

    catalog = pystac_client.Client.open(config.FIRE_STAC_API_URL, modifier=planetary_computer.sign_inplace)
    today = dt.date.today().isoformat()
    search = catalog.search(
        collections=[config.FIRE_STAC_COLLECTION],
        bbox=list(bounds_wgs84),
        datetime=f"{config.FIRE_HISTORY_START}/{today}",
    )
    items = sorted(search.items(), key=lambda it: it.id)
    print(f"Fire history: {len(items)} monthly MODIS items found for {config.FIRE_HISTORY_START} onward")

    if not items:
        print("  No items returned — writing an all-unburned raster and flagging this plainly.")
        last_burn_year = np.zeros(reference.shape, dtype="int16")
    else:
        last_burn_year = np.zeros(reference.shape, dtype="int16")
        study_area_native = None
        latest_item_date = None

        for item in items:
            year = int(item.id.split(".")[1][1:5])  # e.g. "A2025182" -> 2025
            latest_item_date = item.id.split(".")[1]
            href = item.assets["Burn_Date"].href
            da = rioxarray.open_rasterio(href).squeeze("band", drop=True)

            if study_area_native is None or study_area_native.crs != da.rio.crs:
                study_area_native = study_area.to_crs(da.rio.crs)

            try:
                clipped = da.rio.clip_box(*study_area_native.total_bounds)
            except rioxarray.exceptions.NoDataInBounds:
                continue

            aligned = clipped.rio.reproject_match(reference, resampling=Resampling.nearest)
            burned_this_month = aligned.values > 0
            if burned_this_month.any():
                last_burn_year = np.where(burned_this_month, year, last_burn_year)
                print(f"  {item.id}: {burned_this_month.sum()} burned px (year {year})")

        print(f"  Last item processed: {latest_item_date} (this is the true data-currency cutoff, not config.FIRE_HISTORY_END)")

    n_burned_ever = (last_burn_year > 0).sum()
    print(f"Total pixels with a recorded burn in the window: {n_burned_ever} ({n_burned_ever / last_burn_year.size * 100:.2f}% of the study area grid)")

    out = reference.copy(data=last_burn_year)
    out.rio.to_raster(OUT_RASTER)
    print(f"Wrote {OUT_RASTER}")


if __name__ == "__main__":
    main()
