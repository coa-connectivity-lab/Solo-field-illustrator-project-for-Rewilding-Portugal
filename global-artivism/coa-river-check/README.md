# Global Artivism: Côa river line check

Verifies the Côa river line on the three website maps in [global-artivism/img](https://github.com/coa-connectivity-lab/global-artivism/tree/main/img) against OpenStreetMap, using a QGIS project and a reproducible Python workflow.

**Result:** the line is correct and complete, and it matches OSM way for way. The maps are drawn in EPSG:3035, which is turned 11.9° from true north here, while the north arrow points straight up. The Douro isn't drawn either. Details in [analysis.md](analysis.md).

```
README.md      this file
method.md      data sources, steps, how to rerun, limits
analysis.md    findings, tables and recommended fixes to render_maps.py
raw/           inputs: website PNGs + world files (.pgw), bundle river layers, fresh OSM download (2026-09-30)
scripts/       01_fetch_osm → 02_georef_pngs → 03_extract_image_line → 04_compare → 05_build_qgis_project
output/        coa_river_check.qgz (QGIS project), metrics.csv, raster_shift_test.csv,
               image_line.gpkg, gaps.gpkg, hydrorivers_main_stem.gpkg, fig_*.png, qgis_*.png renders
```

Data licences: OpenStreetMap © OpenStreetMap contributors (ODbL); v6 bundle Licence Ouverte 2.0 (Etalab); HydroRIVERS (HydroSHEDS licence).
