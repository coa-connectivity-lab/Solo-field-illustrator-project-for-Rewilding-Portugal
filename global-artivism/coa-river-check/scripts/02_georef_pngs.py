"""Step 2: copy the website map PNGs and the bundle river layers into raw/, and
georeference each PNG with a world file (.pgw, EPSG:3035).

render_maps.py draws each raster at its own extent with bbox_inches="tight",
pad_inches=0.05 at dpi=200, so the image is the raster extent plus a 10 px pad
on every side. Pixel size follows from that; we check x and y agree.

Run from this folder's root:  conda run -n coa python scripts/02_georef_pngs.py
"""
import json
import shutil
from pathlib import Path

import geopandas as gpd
import rioxarray
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
SITE = Path("/home/linda/Documents/myData/global-artivism")
BUNDLE = Path("/home/linda/Documents/myData/coa-eco-connectivity-data-v6/research/eco-connectivity")
RASTER = BUNDLE / "output" / "rasters" / "water_normalized_current.tif"  # all three share one grid
PAD = 10  # px: pad_inches 0.05 * dpi 200

# Bundle vector layers the maps were drawn from
gpkg = BUNDLE / "data" / "processed" / "study_area.gpkg"
for layer in ["coa_river", "coa_catchment_rivers", "study_area"]:
    gpd.read_file(gpkg, layer=layer).to_file(RAW / "bundle_study_area.gpkg", layer=layer, driver="GPKG")

xmin, ymin, xmax, ymax = rioxarray.open_rasterio(RASTER).rio.bounds()
georef = {}
for name in ["movement", "water", "connection"]:
    src = SITE / "img" / f"map-{name}.png"
    dst = RAW / src.name
    shutil.copy2(src, dst)
    w, h = Image.open(dst).size
    px = (xmax - xmin) / (w - 2 * PAD)
    py = (ymax - ymin) / (h - 2 * PAD)
    # world file: pixel size x, rotation, rotation, -pixel size y, centre of upper-left pixel
    ulx, uly = xmin - PAD * px + px / 2, ymax + PAD * py - py / 2
    dst.with_suffix(".pgw").write_text(f"{px:.6f}\n0\n0\n{-py:.6f}\n{ulx:.6f}\n{uly:.6f}\n")
    georef[name] = {"width_px": w, "height_px": h, "pixel_x_m": px, "pixel_y_m": py,
                    "xy_mismatch_pct": 100 * abs(px - py) / px}
    print(name, georef[name])

(RAW / "png_georef.json").write_text(json.dumps(
    {"crs": "EPSG:3035", "raster_bounds": [xmin, ymin, xmax, ymax], "pad_px": PAD, "maps": georef}, indent=2))
