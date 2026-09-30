# Analysis: is the Côa line on the website maps right?

Checked 2026-09-30. Method in [method.md](method.md), all numbers in [output/metrics.csv](output/metrics.csv).

## Short answer

**The river is in the right place and complete.** It is the OpenStreetMap Côa, and it matches a fresh OSM download way for way. The rasters under it are not shifted. **What is wrong is the orientation.** The maps are drawn in the EPSG:3035 grid, which here is turned 11.9° from true north, and the north arrow points straight up. Because the Douro is not drawn, the Côa also stops in the middle of the map with no visible river to flow into. Together these make the line look off even though it isn't.

## Findings

### 1. The maps draw what they were given

The navy pixels extracted from each PNG sit on the bundle `coa_river` line.

| Map | Mean distance, pixel → line | 99th percentile | River drawn (within 150 m) |
| --- | --- | --- | --- |
| movement | 50 m | 109 m | 100 % |
| water | 48 m | 105 m | 100 % |
| connection | 51 m | 111 m | 100 % |

50 m is under one image pixel (70.6 m), and the line is drawn 1.2 pt wide. There is no drawing offset and no missing stretch.

### 2. The bundle line is the real Côa

| Check | Result |
| --- | --- |
| Bundle ways vs fresh OSM (Overpass, 2026-09-30) | 31 vs 31, identical way IDs |
| Length | 143.7 km, both |
| Hausdorff distance, bundle ↔ OSM | 0 m |
| HydroRIVERS main stem | 130.4 km, mean 101 m from OSM, 95 % of points within 252 m (HydroRIVERS is generalised, so it is shorter and cuts meanders) |
| South end | 40.273 N, Serra da Malcata source area |
| North end | 41.083 N, meets the OSM Douro (0 m) at the confluence below Vila Nova de Foz Côa |

Over the OSM basemap, the line follows the mapped channel through Sabugal, the Sabugal reservoir, the Côa gorge and the confluence ([qgis_sabugal_gap_241_m.png](output/qgis_sabugal_gap_241_m.png), [qgis_coa_douro_confluence.png](output/qgis_coa_douro_confluence.png)).

### 3. Two small gaps, not visible at website scale

The 31 ways merge into 3 pieces, not 1:

| Gap | Where | Cause |
| --- | --- | --- |
| 241 m | 40.3356 N, 7.0926 W | Sabugal dam wall. OSM ends the river way on one side of the dam and restarts it on the other. |
| 16 m | 40.8027 N, 7.0187 W | Two OSM ways whose end nodes are not joined |

Both are much smaller than a raster cell (1 km). At the website's scale (14 px per km) the 241 m gap is about 3 px under a line about 3 px wide, so it doesn't show. They only matter if the line is ever used as a network, for example to route along the river. A 16 m gap is worth fixing in OSM itself.

### 4. The rasters are not shifted

The mean raster value along the OSM Côa was computed for every shift of the raster from −5 to +5 km ([fig_raster_shift_test.png](output/fig_raster_shift_test.png)).

| Raster | On-river mean / raster mean | Best shift |
| --- | --- | --- |
| water_normalized_current | 1.05 | 0, 0 |
| multispecies_mean_connectivity | 1.10 | 0, 0 |
| land_normalized_current | 0.98 | no clear peak (a land-movement surface isn't expected to follow the river) |

Water and connection both peak exactly at zero shift. The rasters and the line agree to within a raster cell. Overlaying the georeferenced `map-water.png` on OSM puts Sabugal, Guarda, Pinhel, Vila Nova de Foz Côa and the Douro where the map shows them ([qgis_water_png_on_osm.png](output/qgis_water_png_on_osm.png)).

A side observation, not a line problem: the Côa itself is only mildly elevated in the water current map (5 % above the raster mean). The strongest water corridors are north of the Côa mouth, along the Douro and the Sabor / Vilariça valley. That is a modelling result worth a sentence in the page caption, since readers may expect the named river to be the brightest line.

### 5. The north arrow is wrong by 11.9°

At the map centre (40.666 N, 7.064 W), true north points **11.9° clockwise** from "up" in the EPSG:3035 grid. `render_maps.py` draws "N" straight up, so:

- the whole map, river included, is turned about 12° clockwise compared with a north-up map such as OSM or Google Maps (a feature running due north is drawn leaning to the right)
- the Côa's generally northward course, and the Spanish border, look tilted when compared side by side with a web map

This is the most likely reason the line "does not look right".

## Recommendations for `global-artivism/scripts/render_maps.py`

These are suggestions only. Nothing in `global-artivism` has been changed.

1. **Fix the orientation.** Either:
   - reproject the rasters and the river to **EPSG:3763 (PT-TM06/ETRS89)**, Portugal's national grid, which is almost exactly north-up here, before plotting (`da.rio.reproject(3763)`, `river.to_crs(3763)`), or
   - keep EPSG:3035 and rotate the arrow by the grid convergence (about 11.9° clockwise) so it points to true north.

   The first is cleaner for a public map.
2. **Draw the Douro** (lighter, thinner line; `raw/osm_douro_overpass.geojson` or an OSM extract) so the Côa visibly ends in a river and the strong northern corridors have context.
3. Optional: add two or three place labels (Sabugal, Vila Nova de Foz Côa) so readers can orient themselves.
4. Optional: merge the river ways before plotting (`shapely.ops.linemerge`). It won't change the image, but it makes any later network use honest.

## QGIS project

`output/coa_river_check.qgz` opens in QGIS 3.34+ with relative paths. It expects the v6 bundle at `/home/linda/Documents/myData/coa-eco-connectivity-data-v6/` for the source rasters. Use **View → Bookmarks** to step through the checkpoints. The OSM basemap needs an internet connection.
