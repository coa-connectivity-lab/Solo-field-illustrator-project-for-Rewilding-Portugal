# Agentic Coding GIS Assignment — Côa Valley Livability Score

You are an expert **GIS data scientist, spatial analyst, Python developer, and geospatial research assistant**.

Your task is to complete the spatial-analysis assignment below from scratch.

The final product MUST be a **LIVABILITY SCORE**, as required by the assignment.

Do not rename the concept to "suitability score", "housing suitability score", "naturalist suitability score", or another alternative.

My personal lifestyle priorities should influence the **choice and weighting of livability criteria**, but the final analytical product and terminology must remain a **livability score**.

---

# 1. ORIGINAL ASSIGNMENT

I need to calculate a livability score for all **Apartment Buildings** in a defined city/study area.

The assignment requires:

* identifying apartment buildings;
* selecting meaningful livability criteria;
* calculating spatial metrics for each apartment building;
* combining the metrics into a final livability score;
* producing a GeoPackage containing the enriched apartment-building layer;
* producing a 1–2 page report describing the methodology and validation.

OpenStreetMap may be used to obtain apartment buildings and amenities.

Python packages such as `osmnx`, `geopandas`, `shapely`, `pandas`, `numpy`, and related geospatial libraries may be used.

The assignment specifically encourages an incremental agentic coding workflow:

> Plan and build one step at a time. Validate the output from each step before moving to the next.

Follow that principle strictly.

---

# 2. MY STUDY AREA AND PERSONAL CONTEXT

I want to apply the assignment to the **greater Côa Valley / Guarda region in Portugal**.

I am a naturalist and want to live in this region.

My lifestyle priorities are relevant because the assignment asks me to choose factors that matter to home buyers.

Important factors for me include:

* access to nature;
* access to the Côa River and surrounding landscapes;
* access to parks, protected areas, trails, forests, rivers and other natural areas;
* ability to make field trips by car;
* access to roads and practical driving routes;
* access to parking;
* access to everyday services;
* access to restaurants and food;
* access to healthcare and essential services;
* access to public transport where relevant;
* reasonable rental costs;
* proximity/accessibility to scientists, conservationists and ecological/re-wilding professionals.

I am particularly interested in interacting with scientists and rewilding professionals associated with **Rewilding Portugal**.

Relevant public sources include:

Rewilding Portugal:

https://rewilding-portugal.com/

Rewilding Portugal YouTube channel:

https://www.youtube.com/@rewildingportugal4143

Google Maps reference for Guarda:

https://www.google.com/maps/place/Guarda/@40.5406681,-7.4151791,11z/

Use these sources for context and research, but do not fabricate geographic locations from them.

---

# 3. IMPORTANT: THE OUTPUT IS A LIVABILITY SCORE

The final model must answer:

> **How livable is each apartment building in the greater Côa Valley / Guarda study area, considering the factors that are important to me as a prospective resident?**

The result must therefore be called:

**Livability Score**

and should be normalized to:

**0–100**

where:

* 0 = very low livability according to the selected criteria;
* 100 = very high livability according to the selected criteria.

My naturalist lifestyle should influence the definition of what "livability" means in this particular study.

However, this is still a **livability analysis**, not a specialized "naturalist suitability" model.

Use terminology such as:

* livability;
* livability criteria;
* livability indicators;
* livability components;
* livability score;
* apartment-building livability.

---

# 4. OUTPUT DIRECTORY — VERY IMPORTANT

Save **ALL project work** inside:

```text
/home/linda/Documents/myData/agentic_coding_geospatial/assignment
```

Create this directory if it does not already exist.

Do not scatter project files across the home directory.

The final project should have a structure approximately like:

```text
/home/linda/Documents/myData/agentic_coding_geospatial/assignment/
│
├── notebook/
│   └── coa_valley_livability_analysis.ipynb
│
├── scripts/
│   ├── ...
│   └── ...
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── cache/
│
├── output/
│   ├── coa_valley_livability.gpkg
│   ├── coa_valley_livability_report.pdf
│   ├── tables/
│   └── maps/
│
├── validation/
│   └── ...
│
└── README.md
```

You may modify the internal structure if necessary, but everything must remain inside the `assignment` folder.

The final GeoPackage, report, notebook, scripts, maps, tables, cached data and README must all be accessible from this project directory.

Before beginning the analysis, verify that you can create and write to this directory.

---

# 5. UPLOADED PROJECT MATERIAL

Two ZIP files have been supplied as potentially useful background material:

* `Solo-field-illustrator-project-for-Rewilding-Portugal.zip`
* `eco-connectivity-workflow.zip`

in the assignment folder: /home/linda/Documents/myData/agentic_coding_geospatial/assignment

Inspect them during the reconnaissance phase.

Determine whether they contain:

* GIS datasets;
* notebooks;
* Python scripts;
* ecological connectivity methods;
* maps;
* workflows;
* useful spatial-analysis approaches;
* Rewilding Portugal information.

Reuse useful methods where appropriate, but do not force them into the assignment.

The assignment takes priority over these projects.

---

# 6. DO NOT ONE-SHOT THE ANALYSIS

Work incrementally.

Do NOT immediately generate the complete notebook and final outputs.

Use these phases.

## Phase 1 — Reconnaissance

Inspect:

* the project directory;
* the supplied ZIP files;
* available Python environment;
* relevant installed packages;
* potentially useful datasets;
* appropriate OSM queries;
* geographic boundaries.

Then report what you found.

## Phase 2 — Analysis design

Before implementing the complete workflow, propose:

* study-area definition;
* apartment-building extraction;
* livability criteria;
* datasets;
* spatial thresholds;
* normalization methods;
* weights;
* validation strategy;
* output structure.

Do not proceed to the next major stage until the design is internally coherent.

## Phase 3 — Data acquisition

Build the data acquisition workflow.

Validate:

* feature counts;
* spatial extent;
* CRS;
* geometry types;
* sample attributes.

## Phase 4 — Individual livability indicators

Build indicators one category at a time.

Validate each category before proceeding.

## Phase 5 — Livability scoring

Only after the raw indicators have been checked:

* normalize indicators;
* calculate component scores;
* apply weights;
* calculate the final 0–100 livability score.

## Phase 6 — Validation

Test the results spatially and statistically.

## Phase 7 — Final outputs

Create:

* GeoPackage;
* notebook;
* scripts;
* maps;
* report;
* README.

---

# 7. STUDY AREA

Define a defensible study area for the **greater Côa Valley / Guarda region**.

Do not simply assume that "Guarda municipality" equals the Côa Valley.

Investigate relevant:

* Côa River geography;
* watershed/basin boundaries;
* municipalities;
* protected areas;
* Natura 2000 areas;
* natural areas;
* regional settlements.

Choose an appropriate study-area definition and explain it.

The study area should be practical for an assignment about apartment-building livability.

Avoid making the study area unnecessarily huge simply because additional geographic data are available.

---

# 8. APARTMENT BUILDINGS

Identify apartment buildings using OpenStreetMap where appropriate.

Potential OSM tags include:

```text
building=apartments
```

Investigate whether additional tags or building classifications are needed.

Create a clean apartment-building layer.

Validate:

* number of buildings;
* geometry validity;
* duplicate features;
* CRS;
* spatial distribution;
* representative sample of building tags.

Do not claim that OSM identifies every apartment building in the real world.

Document this limitation.

---

# 9. LIVABILITY CRITERIA

Design the livability score around factors that make sense for residents of the greater Côa Valley.

The following are candidate categories.

## A. Nature and recreation

Potential indicators:

* number of parks nearby;
* distance to nearest park;
* access to forests;
* access to natural areas;
* access to protected areas;
* access to trails;
* access to rivers;
* access to green/open spaces.

Because of my lifestyle, nature access should receive meaningful weight.

However, do not allow this category to completely dominate the score without justification.

---

## B. Côa River access

The Côa River is an important local feature.

Potential indicators:

* distance to Côa River;
* number of accessible river locations within a specified radius;
* distance to river-access roads;
* accessibility to relevant river areas.

Start with simple spatial distance if appropriate.

Network/road distance may be added if it can be implemented reliably.

Do not make network analysis unnecessarily complex.

---

## C. Field-trip / driving accessibility

Because I will need a car for fieldwork, consider:

* proximity to major roads;
* access to regional roads;
* road-network accessibility;
* driving distance to selected natural/river destinations.

If representative fieldwork destinations are used, explain how they were selected.

This is still a **livability criterion**: it represents the practicality of living somewhere while regularly accessing the surrounding region.

---

## D. Parking

Parking is an important residential livability factor for me.

Use available OSM data such as:

* mapped parking facilities;
* parking areas;
* distance to parking;
* parking availability within 500 m / 1 km.

If property-level parking information is available from a reliable source, it may be incorporated.

Do not interpret missing OSM parking data as proof that parking does not exist.

Call this indicator something like:

**Mapped Parking Access**

unless actual property-level parking data are available.

---

## E. Everyday amenities

Include appropriate residential livability indicators such as:

* supermarkets;
* grocery stores;
* restaurants;
* cafés;
* bakeries;
* pharmacies;
* healthcare;
* fuel stations;
* essential services.

Use distance and/or counts within reasonable walking/driving radii.

Avoid allowing restaurant density alone to dominate the model.

---

## F. Public transport

Include:

* bus stops;
* railway stations;
* other public transport where available.

Public transport may receive a smaller weight because car access is more important for my fieldwork, but it remains a legitimate general livability criterion.

---

## G. Scientific, environmental and rewilding community

Where reliable geographic data exist, identify:

* Rewilding Portugal locations;
* conservation organisations;
* ecological restoration projects;
* environmental NGOs;
* scientific institutions;
* universities/research organisations;
* relevant field/research sites.

Calculate appropriate accessibility metrics.

Do not fabricate locations.

If reliable spatial data cannot be obtained, state that the criterion could not be robustly included.

---

## H. Housing affordability

Rent is important to me.

Investigate whether reliable rental/property data can be obtained.

If reliable data are available, incorporate affordability into the livability model.

If they are not:

* do not invent rental prices;
* do not pretend OSM provides rental prices;
* document the limitation;
* optionally create a clearly separated mechanism for adding rental data later.

---

# 10. PROPOSE A WEIGHTING SYSTEM

Develop a defensible weighting scheme.

An initial hypothesis could be:

| Livability dimension              | Initial weight |
| --------------------------------- | -------------: |
| Nature & recreation               |            25% |
| Côa River / natural environment   |            15% |
| Driving / regional accessibility  |            15% |
| Everyday amenities                |            15% |
| Parking                           |            10% |
| Housing affordability             |            10% |
| Public transport                  |             5% |
| Scientific/conservation community |             5% |

These are **starting values, not fixed requirements**.

Evaluate whether they make sense.

Modify them if justified.

The final weights must sum to exactly **100%**.

Explain the rationale.

---

# 11. NORMALIZATION

Do not simply add raw distances and counts together.

Normalize variables to comparable scales.

For example:

### Distance

Higher livability:

```text
shorter distance = higher score
```

### Amenity count

Higher livability:

```text
more amenities = higher score
```

But investigate transformations such as:

* percentile ranking;
* min-max scaling;
* capped counts;
* log transformations;
* threshold-based scoring.

Avoid allowing one extreme urban location to dominate because it has an unusually large number of restaurants or shops.

Document every transformation.

---

# 12. AVOID DOUBLE COUNTING

Analyze correlations among indicators.

For example:

* park proximity;
* natural-area proximity;
* protected-area proximity;
* trail proximity

may overlap.

Likewise:

* restaurant density;
* supermarket density;
* service density

may all be proxies for urban centrality.

Identify excessive redundancy.

If appropriate:

* combine indicators;
* reduce weights;
* remove redundant variables.

Explain the decision.

---

# 13. SIMPLE DISTANCE FIRST

Start with straightforward distance/buffer methods.

For example:

* 500 m;
* 1 km;
* 3 km;
* 5 km;
* 10 km.

Do not begin with complex routing or isochrones unless there is a clear benefit.

If the basic analysis works, optionally add road-network accessibility.

The assignment explicitly says to start simply.

A robust simple model is preferable to a sophisticated model that fails or cannot be reproduced.

---

# 14. VALIDATION

Validation is a required assignment component.

Validate:

## Geometry

Check:

* invalid geometries;
* duplicates;
* CRS;
* unexpected geometry types.

## OSM data

Inspect samples of:

* apartment buildings;
* parks;
* restaurants;
* parking;
* transport;
* natural areas.

## Spatial metrics

Inspect:

* minimum;
* maximum;
* median;
* quartiles;
* missing values.

Map distributions where useful.

## Score validation

Inspect at least:

* several high-scoring buildings;
* several medium-scoring buildings;
* several low-scoring buildings.

For each sample, show:

* location;
* raw indicators;
* normalized indicators;
* component scores;
* final livability score.

Check whether the rankings make geographic and residential sense.

If a result is surprising, investigate it rather than simply accepting it.

---

# 15. SENSITIVITY ANALYSIS

Include at least one sensitivity analysis.

For example, compare:

### Natural-environment emphasis

Higher weighting for:

* nature;
* parks;
* river;
* natural areas.

### Balanced livability

More balanced weighting across:

* nature;
* amenities;
* housing;
* transport;
* parking.

### Practical residential emphasis

Higher weighting for:

* rent;
* parking;
* services;
* roads;
* everyday amenities.

These remain **alternative livability scenarios**, not alternative "suitability scores".

Compare how the apartment-building rankings change.

---

# 16. MAPS

Create diagnostic and final maps.

At minimum:

1. Study area.
2. Apartment buildings.
3. Natural areas / parks.
4. Côa River.
5. Major amenities.
6. Final livability score.
7. High-ranking apartment buildings.

Use maps primarily for analysis and validation.

---

# 17. FINAL GEOPACKAGE

Create:

```text
coa_valley_livability.gpkg
```

inside:

```text
/home/linda/Documents/myData/agentic_coding_geospatial/assignment/output/
```

The main layer should be:

```text
apartment_buildings
```

It must contain:

* building ID;
* geometry;
* relevant OSM attributes;
* raw indicators;
* normalized indicators;
* component scores;
* final `livability_score`;
* rank;
* scenario scores if implemented.

Use clear field names such as:

```text
river_dist_m
river_score
nature_dist_m
nature_score
park_count_1km
park_score
parking_count_1km
parking_score
restaurant_count_1km
restaurant_score
school_dist_m
school_score
amenity_score
fieldwork_access_score
affordability_score
livability_score
livability_rank
```

Do not use cryptic variable names.

---

# 18. REPORT

Create the required **1–2 page report**.

The report should describe:

## Objective

The purpose of the livability analysis.

## Study area

How the greater Côa Valley / Guarda study area was defined.

## Data

Main data sources and dates.

## Methodology

Livability criteria, spatial thresholds, normalization, and weighting.

## Results

Describe the general spatial pattern and high-ranking locations.

Do not overclaim precision.

## Validation

Describe the checks performed.

## Limitations

Discuss:

* OSM completeness;
* apartment-building identification;
* parking data;
* rental data;
* network-distance limitations;
* temporal differences between datasets;
* subjective weighting;
* spatial scale.

## Conclusion

Explain what the livability analysis indicates about residential locations in the greater Côa Valley.

The report should explicitly state that:

> The livability score is a transparent, criteria-based decision-support measure rather than an objective or universal measure of quality of life.

---

# 19. README

Create:

```text
README.md
```

inside the assignment directory.

It should explain:

* project purpose;
* directory structure;
* software requirements;
* how to run the notebook;
* data sources;
* output files;
* reproducibility instructions.

---

# 20. CODE QUALITY

Write clean, readable Python.

Use functions for repeated operations.

Avoid putting the entire workflow into one giant code cell.

Use meaningful variable names.

Add comments explaining non-obvious spatial operations.

Do not hard-code intermediate results.

Use configuration variables for:

* study-area parameters;
* buffer distances;
* scoring thresholds;
* weights;
* output paths.

The project should be reproducible by another GIS analyst.

---

# 21. FILE MANAGEMENT

All generated files must be saved under:

```text
/home/linda/Documents/myData/agentic_coding_geospatial/assignment
```

Use relative paths inside the notebook wherever practical.

Do not accidentally write:

* notebooks;
* scripts;
* GeoPackages;
* maps;
* PDFs;
* temporary project files

to unrelated directories.

Keep raw, processed and output data logically separated.

Do not delete source material unless explicitly necessary.

---

# 22. FINAL QUALITY CHECK

Before declaring the assignment complete, verify:

* [ ] Notebook runs successfully.
* [ ] Apartment buildings are present.
* [ ] Study area is documented.
* [ ] All livability indicators are documented.
* [ ] Indicators are normalized.
* [ ] Weights sum to 100%.
* [ ] Final score ranges from 0–100.
* [ ] Missing data are handled transparently.
* [ ] Validation has been performed.
* [ ] Sensitivity analysis has been performed.
* [ ] GeoPackage opens successfully.
* [ ] Main layer is named `apartment_buildings`.
* [ ] Final field `livability_score` exists.
* [ ] Rankings are populated.
* [ ] Maps are generated.
* [ ] 1–2 page report is generated.
* [ ] README is generated.
* [ ] Scripts are saved.
* [ ] Everything is inside the `assignment` directory.

---

# 23. IMPORTANT AGENT BEHAVIOUR

Do not claim a step succeeded without checking its output.

After each major GIS operation:

1. inspect the result;
2. report feature counts;
3. check CRS;
4. check geometry;
5. inspect attributes;
6. check spatial extent;
7. create a diagnostic visualization when useful.

If an external data source fails:

* diagnose it;
* try a reasonable alternative;
* document the problem;
* do not fabricate data.

If a requested metric cannot be calculated reliably, say so and propose a defensible alternative.

Do not optimize for complexity.

Optimize for:

**correctness + reproducibility + defensibility + clear methodology.**

---

# 24. FIRST ACTION

Start now with **Phase 1 — Reconnaissance**.

Specifically:

1. Verify the assignment directory:
   `/home/linda/Documents/myData/agentic_coding_geospatial/assignment`

2. Inspect the two supplied ZIP files.

3. Inspect the available Python/GIS environment.

4. Investigate appropriate geographic definitions of the greater Côa Valley / Guarda study area.

5. Identify likely data sources.

6. Propose the initial livability indicators and weighting scheme.

7. Explain the planned validation strategy.

8. Do NOT build the entire analysis yet.

9. Do NOT produce the final GeoPackage or report yet.

10. Save any reconnaissance notes/scripts you create inside the assignment directory.

After completing Phase 1, report what you found and what you recommend before proceeding to the next major phase.
