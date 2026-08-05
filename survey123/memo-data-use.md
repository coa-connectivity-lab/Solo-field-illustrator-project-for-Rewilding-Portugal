# Field Data Collection Tool — Survey123

**Status:** Prototype (test data only, not yet used for real fieldwork)
**Author:** Linda Angulo Lopez
**Related:** `coa-connectivity-lab` pipeline (species occurrence, resistance surface, Omniscape connectivity modelling)

## Purpose

A Survey123 form for structured field data collection in the Greater Côa Valley, covering both species observations and physical barriers to wildlife movement. Built to feed directly into the existing connectivity pipeline rather than sit as a separate, incompatible dataset — field entries use the same functional-group taxonomy already defined in `SPECIES_REGISTRY`.

## Structure

**Visit header:** date/time, site name, weather/light conditions, GPS location.

**Species observation** (repeatable): functional group (`large_herbivores`, `decomposers`, `apex_predators`, `mesocarnivores`, `riverine_fish`, `invasive_species` — matching pipeline categories), species/common name, photo, count/abundance estimate, behaviour notes, habitat description, restoration-evidence flag.

**Connectivity barrier** (repeatable): barrier type (road, motorway, fence, dam, weir, culvert, urban edge, agricultural boundary, other), photo, permeability assessment (fully blocking / partially crossable / easily crossable / unknown), notes on effect on movement between habitats.

## Scope

Initial focus: horses and dung beetles at Vale Carapito (testing the herbivore–decomposer restoration link). Expanded to also cover wildcat, native fish, and invasive species, plus the barrier-tracking section — which is intended to ground-truth the resistance-surface assumptions already encoded in `data/interim/base_layers/` (`distance_to_road_m.tif`, `motorway_raster.tif`, `road_raster.tif`, `ruggedness_tri.tif`, `slope_degrees.tif`).

## Data handling

- Hosted under a personal ArcGIS account, not published or shared externally.
- Current data is test/placeholder entries only, used to validate form logic (repeats, dropdowns, photo uploads) before real field use.
- Location data for sensitive species (e.g. wildcat, or other tracked/translocation species) may need coordinate generalisation or restricted internal sharing before any wider use — flagged to the scientific director for guidance, not yet resolved.

## Open items

- Decide on internal data-sharing / location-precision protocol with the scientific director.
- Once real field data exists: build the merge step from Survey123 export into `data/processed/species/` and `data/processed/groups/`, tagged with `source = "field_observation"` to distinguish from GBIF-derived records.