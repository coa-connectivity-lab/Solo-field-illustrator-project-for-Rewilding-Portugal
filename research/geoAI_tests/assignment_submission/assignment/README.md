# Coa Valley Apartment-Building Livability Score

Linda Angulo Lopez, 18 August 2026

## Purpose

A 0-100 livability score for apartment buildings in the greater Coa Valley / Guarda region of Portugal, weighted toward a naturalist resident's priorities: nature and river access, practical driving access for fieldwork, parking, everyday amenities, public transport, and proximity to the Rewilding Portugal community. The score is a transparent, criteria-based decision-support measure, not an objective or universal measure of quality of life -- see the report (`output/coa_valley_livability_report.pdf`) for the full methodology, validation, and limitations.

## Directory structure

```
assignment/
├── notebook/coa_valley_livability_analysis.ipynb   -- end-to-end walkthrough
├── scripts/                                        -- the actual pipeline, one stage per file
│   ├── config.py                                   -- all parameters: study area, thresholds, weights, paths
│   ├── acquire_study_area.py                       -- municipal boundary + apartment-count evidence check
│   ├── acquire_apartment_buildings.py               -- final study area + apartment_buildings layer
│   ├── acquire_indicator_layers.py                  -- nature/river/roads/parking/amenities/transport via OSM
│   ├── acquire_indicator_layers_local_pbf.py         -- fallback path for the same layers via a local OSM extract
│   ├── acquire_ors_driving_distances.py              -- real driving distance/time via OpenRouteService
│   ├── compute_indicators.py                         -- raw indicator calculation per building
│   ├── compute_livability_score.py                   -- normalization, weighting, final score, scenarios
│   ├── validate_results.py                           -- geometry/CRS checks and score spot-checks
│   └── generate_maps.py                              -- the 7 required maps
├── data/
│   ├── raw/           -- municipal boundaries, apartment-count evidence
│   ├── processed/     -- cleaned layers and the indicator table
│   └── cache/         -- the Portugal OSM PBF extract (not committed; see Reproducibility)
├── output/
│   ├── coa_valley_livability.gpkg   -- final deliverable: apartment_buildings layer
│   ├── coa_valley_livability_report.pdf
│   ├── tables/
│   └── maps/           -- the 7 required PNG maps
├── validation/         -- score_spot_checks.md and other diagnostic output
└── README.md
```

## Software requirements

Conda environment `coa` (Python 3.11), already set up with: geopandas, osmnx, shapely, rioxarray, rasterio, fiona, scikit-learn, folium, contextily, matplotlib, pandas, Jupyter. Two packages were added for this project: `fpdf2` (PDF report generation) and `pyrosm` (local OSM-extract parsing, used as a fallback when the public Overpass API was unreliable -- see Data sources below).

An OpenRouteService API key is required for the real driving-distance step. Put it in `assignment/.env` as:
```
ORS_API_KEY=your_key_here
```
This file is gitignored and must not be committed.

## How to run

Run the scripts in order from `assignment/scripts/` (each is independent and re-runnable; most skip work that is already cached on disk):

```bash
conda activate coa
python acquire_study_area.py
python acquire_apartment_buildings.py
python acquire_indicator_layers.py          # falls back to acquire_indicator_layers_local_pbf.py if Overpass is unreachable
python acquire_ors_driving_distances.py
python compute_indicators.py
python compute_livability_score.py
python validate_results.py
python generate_maps.py
```

Or open `notebook/coa_valley_livability_analysis.ipynb` and run all cells, which walks through the same pipeline with narration and inline validation plots.

## Data sources

- OpenStreetMap (buildings, nature areas, the Rio Coa, roads, parking, amenities, transport stops), pulled 2026-08-18. Two access paths were used for different layers: the public Overpass API for nature areas and the Coa river (both succeeded reliably), and a local Geofabrik Portugal extract (`portugal-latest.osm.pbf`, dated 2026-08-17) parsed with `pyrosm` for major roads, parking, amenities, and transport stops, after the public Overpass mirrors proved unreliable (connection failures and timeouts across three different mirrors) for those heavier queries. Both paths ultimately serve the same underlying OSM data.
- OpenRouteService Matrix API, for real driving distance/time from each building to the two field-verified destinations (fieldwork access, rewilding-community proximity), pulled 2026-08-18.
- INE (Portugal's national statistics institute), for regional rental-price context (see report limitations -- no building- or municipality-level rent data exists for this study area, so affordability is not scored, only reported as context).
- Field-verified coordinates for Vale Carapito and Pontao Manuel Jose came from the supplied `Solo-field-illustrator-project-for-Rewilding-Portugal` background material (real GPS fixes recorded during actual site visits, not fabricated).

## Output files

- `output/coa_valley_livability.gpkg` -- layer `apartment_buildings`, one row per building, with every raw indicator, normalized sub-score, component score, `livability_score`, `livability_rank`, and the three sensitivity-scenario scores.
- `output/coa_valley_livability_report.pdf` -- the 1-2 page report.
- `output/maps/01`-`07` -- the required diagnostic and final maps.
- `validation/score_spot_checks.md` -- high/medium/low scoring buildings with their full indicator-to-score breakdown.

## Reproducibility

- All parameters (study area, buffer distances, thresholds, weights, output paths) live in `scripts/config.py` -- nothing is hard-coded elsewhere.
- The Portugal OSM PBF (`data/cache/portugal-latest.osm.pbf`, ~420MB) is not committed; re-download it from `https://download.geofabrik.de/europe/portugal-latest.osm.pbf` if `acquire_indicator_layers_local_pbf.py` is needed again.
- `.env` (the ORS API key) is not committed; each user supplies their own.
- Re-running the full pipeline on a later date will pull a newer OSM/rent snapshot and will not reproduce today's exact figures -- this is expected and documented in the report's limitations.
