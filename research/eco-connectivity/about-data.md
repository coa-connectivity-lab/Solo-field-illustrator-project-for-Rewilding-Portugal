# About the data bundle

**Summary**: How the core data bundle for `notebook/coa_eco_connectivity_story_v6.ipynb` was extracted from the working project, what is in it, and the flaws known so far.
**Last updated**: 2026-09-21 (notebook switch added and tested)

---

## Why a bundle

`.gitignore` excludes `*.tif`, `*.gpkg` and `*.zip`. GitHub therefore holds the notebook, `config.py`, the scripts and the 28 map PNGs, but none of the data. The bundle (`coa-eco-connectivity-data-v6.zip`, about 34 MB zipped, 43 MB unzipped) is meant to be deposited on Recherche Data Gouv and unzipped over a clone of the repository, keeping the folder layout `research/eco-connectivity/{data/processed, output/rasters}`.

## Logic of the extraction

Three steps, each with a rule.

(i) Trace what the notebook touches. Every `read_file` and `open_rasterio` call was followed from the notebook cells into the scripts they call (`generate_maps.py`, `combine_connectivity.py`, `build_tradeoff_maps.py`, `acquire_reserves_and_hunting_zones.py`, `acquire_tourism_sites.py`, `validate_results.py`) and into `config.py`, which defines every path.

(ii) Keep derived products, drop raw inputs. The bundle holds finished layers the story reads (study area, field observations, land tenure, heritage zones, the fire and road-distance covariates, the four resistance surfaces, the 17 connectivity and trade-off rasters). It leaves out anything that is a source download or can be rebuilt from one: GBIF zips, Natura 2000, the DEM-derived base layers, the raw Survey123 export, suitability rasters, `gbif_occurrences.gpkg`.

(iii) Exclude by risk. No raw Survey123 files, no GBIF records (per-record licences, and wolf and wildcat coordinates are generalised or sensitive, see `SENSITIVE_SPECIES` in `config.py`). Field observation attributes were checked: 26 sites, all `sensitive = False`, all `location_precision = exact`, no wildcat species, no personal columns.

Then a README (licence Etalab 2.0, sources, how to use) and `MANIFEST.csv` (path, bytes, sha256) were added, and `environment.yml` was written from the versions in the `coa` conda environment.

## Contents

| Path | What it is |
|---|---|
| `data/processed/study_area.gpkg` | 30 km study area, Côa centreline, traced catchment rivers |
| `data/processed/field_observations.gpkg` | visits, species and barrier observations, Aug 2026 |
| `data/processed/land_tenure.gpkg` | Faia Brava reserve, ICNF hunting zones |
| `data/processed/heritage_protection.gpkg` | Alto Douro, Côa rock-art core |
| `data/processed/covariates/` | `fire_last_burn_year.tif`, `distance_to_road_m.tif` |
| `data/processed/resistance/` | land, land without fire, water, air |
| `output/rasters/` | Omniscape-style current flow, normalised current, multispecies, trade-off classes |

## Limits of the bundle

What you can do with it, with `RUN_PIPELINE = False`:

(i) Run the notebook from top to bottom, regenerate maps 01 to 10, and rerun the combine, trade-off, land-tenure, tourism and validation steps on the shipped layers.

(ii) Inspect and reuse any shipped layer in QGIS or Python, for example to compare, overlay or make new maps.

What you cannot do:

(i) Change the model. Suitability, resistance and connectivity are shipped as finished results. Changing species, dispersal distances, the resistance shape parameter or the study-area buffer needs the raw inputs and `RUN_PIPELINE = True`.

(ii) Rebuild the inputs. There are no GBIF records, Natura 2000, elevation, slope, land cover or imperviousness layers, and no raw Survey123 export.

(iii) Regenerate the Limpopo, Fontainebleau, Camargue, livability and Guarda maps (11 to 28). The notebook only displays their PNGs from the repository. Their data is not in this bundle.

(iv) Treat the layers as final evidence. They come from a single-model, single-parameter run with no uncertainty, over one 30 km study area, with field data from one trip (see Flaws below).

(v) Cite it yet. The DOI does not exist until the production deposit, and the demo instance is not persistent.

## Flaws

### Fixed on 2026-09-21 (branch `share-data-bundle`, not yet pushed)

(i) **The notebook did not run from the bundle alone.** Cells 5, 9, 11, 13, 21 and 25 `%run` the whole upstream pipeline, which needs raw GBIF zips, base layers, Natura 2000, `geoData/CSV.zip`, `research/geoAI_tests/.../coa_river.gpkg` and live web services. Fixed with a `RUN_PIPELINE = False` switch in cell 1 and an `if RUN_PIPELINE:` guard around those `%run` lines. Set it to `True` only if you hold the raw inputs.

(ii) **Test result.** Clean clone, bundle unzipped over it, `data-management` folder hidden, network off: with `RUN_PIPELINE = False` the notebook runs with zero error cells. With `True` the same six cells fail as before, which confirms the switch controls them. Note that `nbconvert --execute` reports success even when cells error, so check cell outputs for `error` entries, not the exit code.

(iii) **Still to do:** commit and push the notebook, `acquire_reserves_and_hunting_zones.py` and `environment.yml`, otherwise collaborators cloning GitHub get the old notebook.

### Reproducibility

(iv) `config.py` has absolute `/home/linda/...` paths (`DATA_MGMT_REPO` and derived). They only matter to the acquire scripts, but the whole upstream half of the pipeline depends on that sibling repository, which collaborators do not have.

(v) The bundle cannot rebuild the upstream layers. Anyone wanting to change the suitability models or resistance surfaces needs the raw inputs, which are not shared.

(vi) Several scripts call live services (Nominatim, ICNF WFS, the national heritage service, Planetary Computer). Results can change or the service can disappear. Only `acquire_reserves_and_hunting_zones.py` has an offline guard (`REFRESH_LAND_TENURE=1` to refresh).

(vii) `environment.yml` is written from the `coa` environment's versions but has not been built from scratch with `conda env create`. Versions are not pinned.

### Data and method limits

(viii) Connectivity is a single best estimate: one Random Forest per group instead of Prima et al.'s four-model ensemble, one shape parameter `c` per group, one Omniscape-style parameter set, no uncertainty. `run_omniscape.py` is a Python solver written to replace Julia Omniscape, and has not been benchmarked against it in this project.

(ix) GBIF records for wolf and wildcat have deliberately generalised coordinates (one wolf record is offset by about 28 km). At a 30 km radius, the strict filter used at national scale would leave almost nothing, so a looser one is used. Suitability for those species is therefore soft.

(x) Fire history is MODIS MCD64A1 burned area at 500 m, from 2015 onwards, which is coarse against the 100 m grid.

(xi) The field data is one trip with 26 sites, so it ground-truths the model only lightly. The Survey123 memo (`survey123/memo-data-use.md`) still lists the location-precision protocol as an open item. The bundle avoids the problem (no sensitive species) but the protocol itself is unresolved.

### Licence and provenance

(xii) Etalab 2.0 is applied to a bundle derived partly from OpenStreetMap (ODbL, share-alike, for the Côa centreline and the Faia Brava boundary). Whether Etalab 2.0 is compatible with that, and with the ICNF and heritage-service terms, has not been checked.

(xiii) The README names Copernicus land cover and imperviousness as sources, but those layers are not shipped, only surfaces derived from them.

(xiv) The demo instance (demo.recherche.data.gouv.fr) is a test environment. Its DOI is not a persistent citation. The README's "How to cite" line stays empty until the production deposit.
