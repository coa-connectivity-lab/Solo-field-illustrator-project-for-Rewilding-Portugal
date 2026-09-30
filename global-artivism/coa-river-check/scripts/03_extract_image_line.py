"""Step 3: pull the drawn river line out of each PNG as georeferenced points.

The line is drawn in navy #10233f (16, 35, 63), which no colour in the RdYlBu_r
ramp comes close to. The scale bar and north arrow (same colour) sit in the
bottom-right corner and are masked out.

Run from this folder's root:  conda run -n coa python scripts/03_extract_image_line.py
Writes output/image_line.gpkg (one layer per map).
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "raw", ROOT / "output"
NAVY = np.array([16, 35, 63])
TOL = 45  # RGB distance; the nearest ramp colour (dark blue 49,54,149) is ~95 away

for name in ["movement", "water", "connection"]:
    png = RAW / f"map-{name}.png"
    rgb = np.asarray(Image.open(png).convert("RGB")).astype(int)
    h, w, _ = rgb.shape
    mask = np.linalg.norm(rgb - NAVY, axis=2) < TOL
    mask[int(h * 0.88):, int(w * 0.78):] = False  # scale bar + north arrow box
    rows, cols = np.nonzero(mask)

    a, _, _, e, c, f = [float(v) for v in png.with_suffix(".pgw").read_text().split()]
    x, y = c + cols * a, f + rows * e
    pts = gpd.GeoDataFrame({"map": name, "row": rows, "col": cols},
                           geometry=gpd.points_from_xy(x, y), crs=3035)
    pts.to_file(OUT / "image_line.gpkg", layer=name, driver="GPKG")
    print(name, len(pts), "line pixels")
