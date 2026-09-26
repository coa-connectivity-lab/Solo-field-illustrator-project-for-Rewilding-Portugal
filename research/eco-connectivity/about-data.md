# About the data bundle

**Summary**: How the core data bundle for `notebook/coa_eco_connectivity_story_v6.ipynb` was extracted from the working project, where it is published, what each file is, and the flaws known so far.
**Last updated**: 2026-09-26 (published on data.gouv.fr, file descriptions added)

---

## Why a bundle

`.gitignore` excludes `*.tif`, `*.gpkg` and `*.zip`. GitHub therefore holds the notebook, `config.py`, the scripts and the 28 map PNGs, but none of the data. The bundle (`coa-eco-connectivity-data-v6`, 29 files, about 34 MB zipped, 43 MB unzipped) is published on data.gouv.fr and is meant to be unzipped over a clone of the repository, keeping the folder layout `research/eco-connectivity/{data/processed, output/rasters}`.

## Where it is published

On 2026-09-26 the bundle was uploaded to data.gouv.fr under the organisation **Côa Connectivity Lab** (website: https://github.com/coa-connectivity-lab). data.gouv.fr replaces Recherche Data Gouv, which was only tried on its demo instance (see flaw xiv).

The organisation describes itself as an open, volunteer research collective building a reproducible ecological connectivity workflow for resource-limited rewilding projects, with the Greater Côa Valley as the worked case study. It uses only open data (GBIF, Natura 2000) and free software (Python, PostgreSQL/PostGIS, QGIS), and publishes the datasets behind the workflow and its notebook so other restoration teams can reuse them. Code: https://github.com/coa-connectivity-lab/eco-connectivity-workflow (MIT).

Collaborators: on the same day, five people were invited to the organisation as **Partial editors**, each with a note pointing to the v6 notebook on `main` (`research/eco-connectivity/notebook/coa_eco_connectivity_story_v6.ipynb`) and saying the data bundle for it is uploaded there. The invitations were still pending on 26 September.

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

## File descriptions

The descriptions used for each resource on data.gouv.fr (all under 200 characters). Paths are relative to `research/eco-connectivity/`. Sources: the bundle's `README.txt`, `config.py` and `scripts/build_tradeoff_maps.py`.

### Documentation

- `README.txt`: How to use the bundle: setup steps, file list, CRS (EPSG:3035, 100 m grid), data sources, licence (Etalab 2.0) and how to cite. Start here.
- `MANIFEST.csv`: Path, size in bytes and SHA-256 checksum of every file in the bundle, to check that downloads are complete and unchanged.

### Vector data

- `data/processed/study_area.gpkg`: Study area (30 km around the Côa river), Côa centreline and catchment rivers (HydroRIVERS). EPSG:3035.
- `data/processed/field_observations.gpkg`: Field data from the August 2026 visits: 26 visited sites, 26 species records and 25 barrier observations with permeability notes. EPSG:4326.
- `data/processed/land_tenure.gpkg`: Land tenure: Faia Brava private reserve and ICNF hunting zones (zonas de caça). Used as constraints for corridor design. EPSG:3035.
- `data/processed/heritage_protection.gpkg`: Heritage areas: UNESCO Alto Douro Wine Region and the Côa Valley rock-art core. Used as a conflict penalty in resistance surfaces. EPSG:3035.

### Covariates

- `data/processed/covariates/distance_to_road_m.tif`: Distance to the nearest road in metres (OpenStreetMap). 100 m grid, EPSG:3035. Input to land resistance and the road trade-off maps.
- `data/processed/covariates/fire_last_burn_year.tif`: Year each cell last burned, 2015-2025 (NASA MODIS MCD64A1 burned area). 100 m grid, EPSG:3035. Adds a fire penalty to land resistance.

### Resistance surfaces

- `data/processed/resistance/land_resistance.tif`: Movement resistance for the Land group (wolf, wildcat, red deer), with fire, field-barrier and heritage penalties. 100 m grid, EPSG:3035.
- `data/processed/resistance/land_resistance_no_fire.tif`: Land group resistance without the fire penalty, to compare with land_resistance.tif and isolate the effect of recent fires. 100 m grid, EPSG:3035.
- `data/processed/resistance/water_resistance.tif`: Resistance for the Water group (otter, Iberian nase, calandino, pond turtle), incl. field-recorded dams, weirs and culverts. 100 m, EPSG:3035.
- `data/processed/resistance/air_resistance.tif`: Resistance for the Air group (griffon vulture, Egyptian vulture, golden eagle), after Prima et al. (2024). 100 m grid, EPSG:3035.

### Connectivity outputs

- `output/rasters/{land,water,air}_current_flow.tif`: Cumulative current flow for each group from circuit-theory connectivity analysis. High values show likely movement routes.
- `output/rasters/{land,water,air}_flow_potential.tif`: Flow potential for each group: current expected if resistance were uniform. Used to normalise current flow.
- `output/rasters/{land,water,air}_normalized_current.tif`: Normalised current for each group (current flow / flow potential). Above 1: channelled corridors; below 1: impeded movement.
- `output/rasters/multispecies_mean_connectivity.tif`: Multispecies connectivity: species-count-weighted mean of the Land, Water and Air normalised current. Fire- and catchment-aware.
- `output/rasters/multispecies_max_connectivity.tif`: Multispecies connectivity: highest normalised current across the Land, Water and Air groups in each cell.

### Road and waterway trade-offs

- `output/rasters/road_barrier_severity.tif`: Road barrier severity for wildlife: 1 / (1 + distance to road in km). The closer to a road, the higher the value.
- `output/rasters/road_access_value.tif`: Eco-tourism access value: proximity kernel (5 km decay) around 6 visitor sites, e.g. Penascosa rock art and river beaches.
- `output/rasters/road_tradeoff_class.tif`: Road trade-off classes from median splits of barrier severity and access value: conservation priority, compatible access or conflict.
- `output/rasters/waterway_barrier_severity.tif`: Waterway barrier severity, taken from the Water group resistance surface (includes field-recorded dams, weirs and culverts).
- `output/rasters/waterway_access_value.tif`: Waterway access value: proximity kernel around the same visitor sites, most of them river beaches (praias fluviais).
- `output/rasters/waterway_tradeoff_class.tif`: Waterway trade-off classes from median splits of barrier severity and access value: conservation priority, compatible access or conflict.

## Limits of the bundle

What you can do with it, with `RUN_PIPELINE = False`:

(i) Run the notebook from top to bottom, regenerate maps 01 to 10, and rerun the combine, trade-off, land-tenure, tourism and validation steps on the shipped layers.

(ii) Inspect and reuse any shipped layer in QGIS or Python, for example to compare, overlay or make new maps.

What you cannot do:

(i) Change the model. Suitability, resistance and connectivity are shipped as finished results. Changing species, dispersal distances, the resistance shape parameter or the study-area buffer needs the raw inputs and `RUN_PIPELINE = True`.

(ii) Rebuild the inputs. There are no GBIF records, Natura 2000, elevation, slope, land cover or imperviousness layers, and no raw Survey123 export.

(iii) Regenerate the Limpopo, Fontainebleau, Camargue, livability and Guarda maps (11 to 28). The notebook only displays their PNGs from the repository. Their data is not in this bundle.

(iv) Treat the layers as final evidence. They come from a single-model, single-parameter run with no uncertainty, over one 30 km study area, with field data from one trip (see Flaws below).

(v) Cite it with a DOI. data.gouv.fr does not issue DOIs, so cite the dataset URL on data.gouv.fr instead.

## Flaws

### Fixed on 2026-09-21 (branch `share-data-bundle`, not yet pushed)

(i) **The notebook did not run from the bundle alone.** Cells 5, 9, 11, 13, 21 and 25 `%run` the whole upstream pipeline, which needs raw GBIF zips, base layers, Natura 2000, `geoData/CSV.zip`, `research/geoAI_tests/.../coa_river.gpkg` and live web services. Fixed with a `RUN_PIPELINE = False` switch in cell 1 and an `if RUN_PIPELINE:` guard around those `%run` lines. Set it to `True` only if you hold the raw inputs.

(ii) **Test result.** Clean clone, bundle unzipped over it, `data-management` folder hidden, network off: with `RUN_PIPELINE = False` the notebook runs with zero error cells. With `True` the same six cells fail as before, which confirms the switch controls them. Note that `nbconvert --execute` reports success even when cells error, so check cell outputs for `error` entries, not the exit code.

(iii) **Done:** the notebook, `acquire_reserves_and_hunting_zones.py` and `environment.yml` are on `main`, so collaborators cloning GitHub get the notebook with the switch.

### Before or just after upload (2026-09-26)

(iii-a) **`README.txt` still points to Recherche Data Gouv.** Its "How to cite" section needs to say data.gouv.fr, with the dataset URL in place of the DOI placeholder.

(iii-b) **`field_observations.gpkg` checked again before publishing:** no wildcat or other sensitive-species records, and no site flagged sensitive.

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

(xii) Etalab 2.0 is applied to a bundle derived partly from OpenStreetMap (ODbL, share-alike, for the Côa centreline and the Faia Brava boundary). Decision on 2026-09-26: the OpenStreetMap-derived files (`land_tenure.gpkg`, `study_area.gpkg`, the road layers) stay under ODbL, and the dataset description on data.gouv.fr must say so. Compatibility with the ICNF and heritage-service terms has still not been checked. GBIF records are not in the bundle.

(xiii) The README names Copernicus land cover and imperviousness as sources, but those layers are not shipped, only surfaces derived from them.

(xiv) The demo instance (demo.recherche.data.gouv.fr) was a test environment and its DOI is not a persistent citation. It is superseded by the data.gouv.fr deposit (see "Where it is published").
