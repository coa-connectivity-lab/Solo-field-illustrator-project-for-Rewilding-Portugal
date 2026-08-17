# Session Report — London Crime Hotspot Analysis Planning

**Date:** 2026-08-17

## What was asked

The session began with a request to plan a "crime hotspot analysis in London." Partway through requirements-gathering, the request was called off ("never mind, I don't want to follow through"). No code or plan file was finalized or executed during this session — it consisted entirely of discussion, discovery, and requirements-gathering.

## Key discovery

Exploring the project directory (`/home/linda/Documents/myData/agentic_coding_geospatial`) turned up an **existing, already-working hotspot analysis pipeline** — this was not a greenfield project as initially assumed:

- **`data/london_crime_2024_eda/eda_london_crime_2024.py`** — EDA on 2024 City of London Police crime data: summary stats, data-quality flags, crime-type bar chart/treemap, monthly trend charts, and a GeoJSON export of all 9,028 geocoded crimes.
- **`data/london_crime_2024_hotspots/hotspots_london_crime_2024.py`** — a full hotspot pipeline for theft-type crimes: LSOA aggregation, theft rate per 1,000 population (via ONS boundaries + Census 2021 population), Getis-Ord Gi* hotspot statistics (`esda`/`libpysal`), a KDE density surface, static choropleth maps, a ranked summary CSV, and an already-generated self-contained interactive map (`theft_hotspots_map.html`).
- Methodology is grounded in `documents/hotspots.pdf` (NIJ, "Mapping Crime: Understanding Hot Spots").
- **Important caveat already baked into both scripts**: the data is **City of London Police only** (the small financial-district force), *not* Metropolitan Police / Greater London-wide, despite folder naming.

## Decisions made during Q&A

Through several rounds of clarification, the discussion converged on extending the existing pipeline (not rebuilding it), by:

- Adding **Burglary** and **Vehicle crime** as additional hotspot categories alongside the existing theft group.
- Widening the time range beyond 2024.
- Keeping the output as a single self-contained HTML map (folium), with layer toggles for the new category/time dimensions.
- Using the existing **`claude_code_workshop`** conda environment — confirmed it already has everything needed (geopandas, esda, libpysal, folium, scipy, scikit-learn, rioxarray, xarray, requests), so no new installs were required.

## Technical finding that changed scope

While verifying the data-fetch approach, a direct query to the live data.police.uk API found:

- It only retains a **rolling 36-month window** — as of 2026-08-17, the earliest available month is **2023-07**. Full-year 2022 and Jan–Jun 2023 data are **not obtainable** from the live API anymore.
- The live API's JSON schema differs from the bulk CSV files already in the project (no LSOA code, lowercase-hyphenated category names, no force/outcome fields in the same shape) — any new fetch would need a small adapter (spatial join to LSOA polygons, category-name mapping) to normalize into the existing CSV schema.

Based on this, the year range was revised to **2023-07 through 2024-12 (18 months)**, the maximum available overlap with the original request.

## Work in progress at the time of cancellation

A design pass was dispatched to work out the concrete file-by-file extension (new fetch script, generalized category-group pipeline, time-slicing approach for the map, layer-naming scheme). It had not returned a result before the request was called off, so **no implementation plan was finalized**.

## Net outputs from this session

- No new files, scripts, or data were written to the project.
- No existing files were modified.
- The only artifact from this session is this report, plus the requirements/findings captured above should the hotspot extension be picked up again later.

## Follow-up session (later, 2026-08-17) — theft hotspot GeoJSON export

Picked back up later the same day with a narrower, concrete ask: generate a GeoJSON version of the hotspot data shown in `theft_hotspots_map.html`, saved to `output/`.

**Investigation:** the HTML map itself is a poor source to scrape — folium wrote one bare `GeoJson` geometry per LSOA per layer (198 total), with all attributes (theft count, rate, Gi* z-scores, category) embedded only as text inside each popup, not as GeoJSON `properties`. Instead, the same pipeline run already writes the exact underlying data as two clean files next to the HTML: `external/lsoa_boundaries_mesh.geojson` (99 LSOA polygons) and `theft_hotspot_lsoa_summary.csv` (full attribute table, keyed by `lsoa_code`). Joining these with GeoPandas reproduces the map's data exactly, with proper properties, no network calls, and no HTML parsing.

**New script:** `data/london_crime_2024_hotspots/export_hotspots_geojson.py` — merges the mesh and summary CSV on LSOA code and writes `output/theft_hotspots_lsoa.geojson` (99 features: theft counts, population, rate per 1,000, and both rate- and raw-count Gi* z-scores/p-values/categories).

**Follow-up issue — "this is not a hotspot analysis at all":** traced to a *pre-existing* QGIS project, `output/crime_hotspots_london.qgz` (not created by either session), which loads two unrelated raw layers — the full 9,028-point EDA crime dataset and the bare LSOA mesh with no attributes — both with default single-symbol styling. It doesn't reference the new GeoJSON at all. Fix (per user's choice): leave that `.qgz` alone, and instead add a QGIS style sidecar, `output/theft_hotspots_lsoa.qml`, generated by the same export script, importing `GI_STAR_LABELS`/`GI_STAR_COLORS` directly from `hotspots_london_crime_2024.py` so the categorized-by-`rate_category` styling matches `theft_gi_star_rate.png` exactly (verified: 7 categories, correct labels and hex colors).

**Web GIS follow-up:** user uploaded the GeoJSON to a browser-based GIS tool (`https://web.geolibre.app/`) and it rendered identically to the unstyled `lsoa_boundaries_mesh.geojson`. Confirmed this is expected, not a bug — the `.qml` sidecar only works in QGIS, and plain GeoJSON carries no styling for any viewer. Re-verified the exported GeoJSON's properties are intact (`rate_category`, `raw_category`, counts, rates, z-scores all present per feature). Advised checking the attribute popup on the site to confirm the data came through, then applying categorized styling manually in geolibre.app's own style panel using the same 7 category/color pairs.

### Net outputs from this follow-up session

- New: `data/london_crime_2024_hotspots/export_hotspots_geojson.py`
- New: `output/theft_hotspots_lsoa.geojson`
- New: `output/theft_hotspots_lsoa.qml`
- No existing pipeline files (`hotspots_london_crime_2024.py`, cached `external/` data, `theft_hotspots_map.html`, etc.) or the pre-existing `output/crime_hotspots_london.qgz` were modified.
