# Note: Côa river line check and the preprint (2026-09-30)

**Status:** open, decide in late October 2026 whether to publish a v0.2 on Zenodo or add a note. v0.1 stays public either way.

## Background

The Côa line on the gallery maps looked wrong, so it was checked against OpenStreetMap in QGIS. Full method, data, QGIS project and scripts are in `global-artivism/coa-river-check/` in this repo (commit `4c9d5b0`, merged to `main`). Findings are in `analysis.md`.

**Result:** the river line and the rasters are correct. The river matches a fresh OSM download way for way and is drawn within 50 m, and the rasters are not offset. The problem is orientation: the gallery maps are drawn in EPSG:3035, where true north points **11.9° clockwise** of "up" in this area, but the north arrow points straight up. The Douro is not drawn.

## Where this touches `article.md`

| Place | What to consider |
| --- | --- |
| Figures 4, 5 and 7 (`figures/fig04_map_movement.png`, `fig05_map_water.png`, `fig07_map_connection.png`), captions at lines 157, 159, 167 | These are the gallery maps. The north arrow is 11.9° off. Either replace them with redrawn north-up maps (EPSG:3763) or add to each caption: "Grid north (EPSG:3035); true north is about 12° clockwise." |
| Section on the gallery (line 179): "given only the Côa river, a 10 km scale bar and a north arrow" | If the maps are redrawn, this can stay. If not, say the arrow shows grid north. |
| Results text for land and water (lines 151, 153): "north-south", "east-west", "north-east trending" | These directions are read off the EPSG:3035 grid. At 12° they are still broadly right, but "north-east trending" bands are closer to north-north-east in true bearings. Worth a check if the figures change. |
| Line 41: "All raster work uses ... EPSG:3035 at 100 m resolution" | **Needs checking, separate from the arrow.** The v6 bundle rasters used for the gallery maps (`output/rasters/*_normalized_current.tif`, `multispecies_mean_connectivity.tif`) are 1,000 m cells, 87 × 152. Either the bundle ships a resampled copy, or the resolution statement or the figure source needs correcting. |
| Line 35: study area built from the "Côa river centreline (OpenStreetMap)" | Confirmed. The bundle `coa_river` layer is exactly the current OSM Côa (31 ways, 143.7 km). Two small gaps (241 m at the Sabugal dam, 16 m) don't affect a 30 km buffer. |

## Options

1. **v0.2**: redraw Figures 4, 5 and 7 north-up (together with the website maps, see `global-artivism/data/NOTE-2026-09-30-coa-river-check.md` in the site repo), fix the resolution statement if needed, and add a changelog line.
2. **Note only**: add a Zenodo "Notes" field or comment: "Figures 4, 5 and 7 show grid north (EPSG:3035); true north is about 12° clockwise."
3. **Hold** until after Global Artivism Month and fold this into a later version.
