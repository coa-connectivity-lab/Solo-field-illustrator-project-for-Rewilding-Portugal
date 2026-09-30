"""Step 4: compare the drawn line, the bundle river, fresh OSM and HydroRIVERS,
test the rasters for an offset, and check the north arrow.

Run from this folder's root:  conda run -n coa python scripts/04_compare.py
Writes output/metrics.csv, output/gaps.gpkg, output/hydrorivers_main_stem.gpkg,
output/raster_shift_test.csv and figures output/fig_*.png
"""
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rioxarray
from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import linemerge, unary_union

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "raw", ROOT / "output"
BUNDLE = Path("/home/linda/Documents/myData/coa-eco-connectivity-data-v6/research/eco-connectivity")
RASTERS = BUNDLE / "output" / "rasters"
MAPS = {"movement": "land_normalized_current.tif", "water": "water_normalized_current.tif",
        "connection": "multispecies_mean_connectivity.tif"}
M = 3763  # PT-TM06/ETRS89, metres, for distances
metrics = []


def add(group, metric, value, note=""):
    metrics.append({"group": group, "metric": metric, "value": value, "note": note})
    print(f"{group:12s} {metric:45s} {value}  {note}")


def sample_along(geom, step=100):
    """Points every `step` metres along a (multi)line."""
    parts = getattr(geom, "geoms", [geom])
    return [p.interpolate(d) for p in parts for d in np.arange(0, p.length, step)]


gpkg = RAW / "bundle_study_area.gpkg"
bundle = gpd.read_file(gpkg, layer="coa_river").to_crs(M)
hyd = gpd.read_file(gpkg, layer="coa_catchment_rivers").to_crs(M)
osm = gpd.read_file(RAW / "osm_coa_overpass.geojson").to_crs(M)
douro = gpd.read_file(RAW / "osm_douro_overpass.geojson").to_crs(M)
b_geom, o_geom = unary_union(bundle.geometry), unary_union(osm.geometry)

# --- A. did the script draw what it was given? image pixels vs bundle line
for name in MAPS:
    img = gpd.read_file(OUT / "image_line.gpkg", layer=name).to_crs(M)
    d = img.distance(b_geom)
    add("image", f"{name}: pixel→bundle mean distance (m)", round(d.mean(), 1))
    add("image", f"{name}: pixel→bundle 99th pct distance (m)", round(d.quantile(0.99), 1))
    img_u = unary_union(img.geometry)
    along = sample_along(b_geom)
    covered = np.mean([p.distance(img_u) < 150 for p in along])
    add("image", f"{name}: bundle river drawn (share within 150 m)", round(covered, 3))

# --- B. is the bundle river the real Côa? vs fresh OSM and HydroRIVERS
add("osm", "bundle ways", len(bundle))
add("osm", "fresh OSM ways", len(osm))
add("osm", "way IDs only in bundle", len(set(bundle["id"]) - set(osm["id"])))
add("osm", "way IDs only in fresh OSM", len(set(osm["id"]) - set(bundle["id"])))
add("osm", "bundle length (km)", round(b_geom.length / 1000, 1))
add("osm", "fresh OSM length (km)", round(o_geom.length / 1000, 1))
add("osm", "Hausdorff bundle↔OSM (m)", round(b_geom.hausdorff_distance(o_geom), 1))

# HydroRIVERS main stem: walk upstream from the mouth, always taking the larger upstream area
seg = hyd.set_index("HYRIV_ID")
cur = seg["DIST_DN_KM"].idxmin()
stem = [cur]
while True:
    up = seg[seg["NEXT_DOWN"] == cur]
    if up.empty:
        break
    cur = up["UPLAND_SKM"].idxmax()
    stem.append(cur)
main = seg.loc[stem].reset_index()
main.to_file(OUT / "hydrorivers_main_stem.gpkg", driver="GPKG")
m_geom = unary_union(main.geometry)
add("hydrorivers", "main stem length (km)", round(m_geom.length / 1000, 1), "15 arc-sec network, generalised")
d = pd.Series([p.distance(m_geom) for p in sample_along(o_geom, 250)])
add("hydrorivers", "OSM→HydroRIVERS mean distance (m)", round(d.mean(), 1))
add("hydrorivers", "OSM→HydroRIVERS 95th pct distance (m)", round(d.quantile(0.95), 1))

# --- C. gaps in the bundle line
merged = linemerge(b_geom)
parts = sorted(getattr(merged, "geoms", [merged]), key=lambda g: -g.length)
add("gaps", "connected pieces after merge", len(parts))
gaps = []
for i, a in enumerate(parts):
    for b in parts[i + 1:]:
        ends_a = [Point(a.coords[0]), Point(a.coords[-1])]
        ends_b = [Point(b.coords[0]), Point(b.coords[-1])]
        pa, pb = min(((x, y) for x in ends_a for y in ends_b), key=lambda t: t[0].distance(t[1]))
        gaps.append({"gap_m": pa.distance(pb), "geometry": pa})
gaps = gpd.GeoDataFrame(gaps, crs=M).sort_values("gap_m").head(len(parts) - 1)
for _, g in gaps.iterrows():
    ll = gpd.GeoSeries([g.geometry], crs=M).to_crs(4326).iloc[0]
    add("gaps", "gap length (m)", round(g.gap_m, 1), f"at {ll.y:.5f} N, {ll.x:.5f} E")
for p in parts:
    add("gaps", "piece length (km)", round(p.length / 1000, 2))
gaps.to_crs(3035).to_file(OUT / "gaps.gpkg", driver="GPKG")

# Ends: source (south) and mouth (north) against the Douro
ll = bundle.to_crs(4326).total_bounds
add("ends", "south end latitude", round(ll[1], 4), "source, Serra da Malcata ~40.27 N")
add("ends", "north end latitude", round(ll[3], 4), "mouth near Vila Nova de Foz Côa ~41.08 N")
northmost = max((Point(c) for g in parts for c in (g.coords[0], g.coords[-1])), key=lambda p: p.y)
add("ends", "north end → OSM Douro distance (m)", round(northmost.distance(unary_union(douro.geometry)), 1))

# --- D. are the rasters offset? mean value along the OSM Côa for grid shifts of -5..5 km
pts3035 = gpd.GeoSeries(sample_along(o_geom, 200), crs=M).to_crs(3035)
px, py = pts3035.x.values, pts3035.y.values
shift_rows = []
for name, tif in MAPS.items():
    da = rioxarray.open_rasterio(RASTERS / tif, masked=True).squeeze()
    base = float(da.mean())
    for dx in range(-5000, 5001, 1000):
        for dy in range(-5000, 5001, 1000):
            vals = da.interp(x=("p", px + dx), y=("p", py + dy), method="nearest")
            shift_rows.append({"map": name, "dx_m": dx, "dy_m": dy,
                               "mean_on_river": float(vals.mean()), "raster_mean": base})
shift = pd.DataFrame(shift_rows)
shift.to_csv(OUT / "raster_shift_test.csv", index=False)
for name in MAPS:
    s = shift[shift["map"] == name]
    zero = s[(s.dx_m == 0) & (s.dy_m == 0)].iloc[0]
    best = s.loc[s["mean_on_river"].idxmax()]
    add("raster", f"{name}: on-river mean / raster mean (no shift)",
        round(zero.mean_on_river / zero.raster_mean, 2))
    add("raster", f"{name}: best shift dx,dy (m)", f"{int(best.dx_m)},{int(best.dy_m)}",
        f"ratio {best.mean_on_river / best.raster_mean:.2f}")

# --- E. north arrow: angle of true north in the EPSG:3035 grid at the map centre
da = rioxarray.open_rasterio(RASTERS / MAPS["water"]).squeeze()
xmin, ymin, xmax, ymax = da.rio.bounds()
to_ll = Transformer.from_crs(3035, 4326, always_xy=True)
to_grid = Transformer.from_crs(4326, 3035, always_xy=True)
lon, lat = to_ll.transform((xmin + xmax) / 2, (ymin + ymax) / 2)
x0, y0 = to_grid.transform(lon, lat)
x1, y1 = to_grid.transform(lon, lat + 0.1)
angle = np.degrees(np.arctan2(x1 - x0, y1 - y0))
add("north", "true north vs grid up (deg, + = clockwise)", round(angle, 2),
    f"centre {lat:.3f} N {lon:.3f} E")

pd.DataFrame(metrics).to_csv(OUT / "metrics.csv", index=False)

# --- Figures ---------------------------------------------------------------
lay = lambda g: gpd.GeoSeries([g], crs=M).to_crs(3035)
for name in MAPS:
    png = RAW / f"map-{name}.png"
    a, _, _, e, c, f = [float(v) for v in png.with_suffix(".pgw").read_text().split()]
    im = plt.imread(png)
    h, w = im.shape[:2]
    fig, ax = plt.subplots(figsize=(7, 12), dpi=150)
    ax.imshow(im, extent=(c - a / 2, c + a * (w - 0.5), f + e * (h - 0.5), f - e / 2), alpha=0.55)
    lay(o_geom).plot(ax=ax, color="#00bcd4", linewidth=2.2, label="OSM Côa (fresh, Overpass)")
    lay(b_geom).plot(ax=ax, color="#10233f", linewidth=0.8, label="bundle coa_river")
    lay(m_geom).plot(ax=ax, color="#e91e63", linewidth=1, linestyle="--", label="HydroRIVERS main stem")
    gpd.GeoSeries(douro.geometry, crs=M).to_crs(3035).plot(ax=ax, color="#3f51b5", linewidth=1.5,
                                                          label="OSM Douro")
    gaps.to_crs(3035).plot(ax=ax, color="red", markersize=60, marker="x", label="gap in bundle line")
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.legend(loc="lower left", fontsize=7)
    ax.set_title(f"map-{name}.png georeferenced, with reference rivers (EPSG:3035)", fontsize=9)
    fig.savefig(OUT / f"fig_overlay_{name}.png", bbox_inches="tight")
    plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(12, 4), dpi=150)
for ax, name in zip(axes, MAPS):
    s = shift[shift["map"] == name].pivot(index="dy_m", columns="dx_m", values="mean_on_river")
    ax.imshow(s.values, origin="lower", extent=(-5.5, 5.5, -5.5, 5.5), cmap="viridis")
    ax.plot(0, 0, "r+", markersize=12)
    ax.set_title(f"{name}: mean value on OSM Côa\nfor raster shifts (km)", fontsize=9)
    ax.set_xlabel("dx (km)"); ax.set_ylabel("dy (km)")
fig.tight_layout()
fig.savefig(OUT / "fig_raster_shift_test.png")
print("done")
