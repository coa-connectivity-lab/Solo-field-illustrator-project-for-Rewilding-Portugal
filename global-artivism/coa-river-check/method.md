# Method

Checking the Côa river line on the three Global Artivism website maps (`global-artivism/img/map-movement.png`, `map-water.png`, `map-connection.png`) against OpenStreetMap.

## Question

Is the river line drawn on the website maps in the right place, and complete? If it looks wrong, is the cause the line, the rasters under it, or the map framing?

## Data

| Data | Source | Where |
| --- | --- | --- |
| Website map PNGs, 1252 × 2172 px | `global-artivism/img/`, rendered by `global-artivism/scripts/render_maps.py` | `raw/map-*.png` |
| River line drawn on the maps (`coa_river`, 31 OSM ways) | v6 bundle, `data/processed/study_area.gpkg` ([data.gouv.fr](https://www.data.gouv.fr/datasets/coa-valley-eco-connectivity-v6), Etalab 2.0; underlying data © OpenStreetMap contributors, ODbL) | `raw/bundle_study_area.gpkg` |
| HydroRIVERS Côa network (`coa_catchment_rivers`) | same bundle; HydroSHEDS HydroRIVERS v1.0 | `raw/bundle_study_area.gpkg` |
| Study area polygon | same bundle | `raw/bundle_study_area.gpkg` |
| Fresh OSM Côa and Douro | Overpass API, downloaded 2026-09-30 (query and time in `raw/osm_query.txt`), © OpenStreetMap contributors, ODbL | `raw/osm_coa_overpass.geojson`, `raw/osm_douro_overpass.geojson` |
| Connectivity rasters, 1 km, EPSG:3035 | v6 bundle, `output/rasters/` | read in place, not copied |
| OpenStreetMap Standard tiles | tile.openstreetmap.org | basemap in the QGIS project |

## Steps

1. **Independent OSM download** (`scripts/01_fetch_osm.py`). Overpass query for `waterway=river` ways named "Côa"/"Coa", and separately "Douro", in the box 40.2–41.2 N, 7.3–6.7 W. Falls back to mirror servers when the main one times out.
2. **Georeference the PNGs** (`scripts/02_georef_pngs.py`). `render_maps.py` draws each raster at its own extent with `bbox_inches="tight"`, `pad_inches=0.05` and `dpi=200`, so every PNG is the raster extent plus a 10 px margin. That gives an exact world file (`.pgw`, EPSG:3035): 70.617 m per pixel across, 70.632 m down. The two agree to 0.02 %, under half a pixel over the full image height, which confirms the framing assumption.
3. **Extract the drawn line** (`scripts/03_extract_image_line.py`). Pixels within RGB distance 45 of the line colour `#10233f` are kept. No colour in the RdYlBu_r ramp is closer than about 95. The scale bar and north arrow corner is masked out. Pixel centres are converted to EPSG:3035 points.
4. **Compare** (`scripts/04_compare.py`, distances in EPSG:3763 PT-TM06):
   - image pixels vs bundle `coa_river`: mean and 99th-percentile distance, and the share of the river (sampled every 100 m) that has a drawn pixel within 150 m
   - bundle `coa_river` vs fresh OSM: way IDs, length, Hausdorff distance
   - OSM vs HydroRIVERS main stem, traced upstream from the mouth by always taking the branch with the larger upstream area
   - gaps: merge the bundle ways and measure the distance between the loose ends
   - ends: latitude of the source and mouth, distance from the north end to the OSM Douro
   - raster offset test: mean raster value sampled every 200 m along the OSM Côa, repeated for every shift of the raster from −5 to +5 km in 1 km steps. If the rasters were misplaced, the best shift would be away from (0, 0).
   - north arrow: angle between true north and "up" in the EPSG:3035 grid at the map centre
5. **QGIS project** (`scripts/05_build_qgis_project.py`, system PyQGIS 3.34, headless). Project CRS EPSG:3035 (same as the website maps), with OSM basemap, georeferenced PNGs at 60 % opacity, source rasters, the bundle line, fresh OSM, HydroRIVERS, Douro, gap points and the extracted image pixels. Bookmarks cover the source, Sabugal, both gaps, Penascosa / Foz Côa, the Douro confluence and the whole area. Each bookmark is rendered over the OSM basemap to `output/qgis_*.png`.

## Rerun

```bash
cd global-artivism/coa-river-check
conda run -n coa python scripts/01_fetch_osm.py        # network; optional, raw/ already holds the 2026-09-30 download
conda run -n coa python scripts/02_georef_pngs.py
conda run -n coa python scripts/03_extract_image_line.py
conda run -n coa python scripts/04_compare.py
QT_QPA_PLATFORM=offscreen python3 scripts/05_build_qgis_project.py   # system python with PyQGIS
```

Steps 2–5 were rerun from an empty `output/` and gave identical metrics.

## Limits

- The rasters are 1 km cells, so any offset smaller than about 500 m would not show in the shift test.
- OSM is the reference here. It was checked against HydroRIVERS, which is a separate, coarser (15 arc-second) data set, not against surveyed ground truth.
- The fresh OSM download reflects OSM on 2026-09-30. Later edits to OSM may change the way count.
