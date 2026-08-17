# A research proposal
Linda Angulo Lopez, 11 August 2026

Estimating the relative contribution of rivers, canyons, and roads to landscape connectivity in the Greater Côa Valley

1. Background

The Greater Côa Valley functions as a wildlife corridor linking Mediterranean and Atlantic-influenced ecosystems across 318,000 hectares of northern Portugal. Rewilding Portugal and partner organisations have documented the corridor's value in general terms, focal species, hectares under restoration, reintroduction numbers, but the relative weight of the landscape's own physical structure in enabling or constraining that connectivity has not been isolated. Three features recur across every site visited during this fieldwork: the river itself as both corridor and barrier depending on scale, the steep canyon topography that shapes the valley's ecological refugia, and the road network that cuts across both. This proposal sets out to quantify each feature's independent contribution to landscape connectivity, rather than treating them as an undifferentiated background to species occurrence.

2. Research questions

(i) What proportion of overall landscape resistance in the Greater Côa Valley is attributable to river/hydrological features, to canyon/terrain ruggedness, and to the road network, considered separately?

(ii) Do rivers and canyons function primarily as corridors or as barriers, and does this differ by functional group, aquatic, terrestrial, avian?

(iii) Where do roads intersect river and canyon corridors, and do these intersections constitute the landscape's most significant connectivity pinch points?

(iv) How sensitive is the overall connectivity model to each layer, does removing roads from the resistance surface change the predicted current flow more than removing canyon ruggedness, or less?

3. Study area

The Greater Côa Valley, Beira Interior, Portugal, bounded by the Malcata mountains to the south and the Douro valley to the north. Field data collected across five sites, Almeida/Pontão Manuel José, Vale Carapito, Paul de Toirões, Ribeira do Mosteiro, and the Nascente do Rio Côa near Fóios, supplemented by GBIF occurrence data for the region's verified focal species.

4. Data

(i) Hydrology: river network and stream order from existing GIS layers, plus field-confirmed barrier points, weirs, dams, from Survey123 records.

(ii) Terrain: digital elevation model, slope, and a ruggedness index (terrain ruggedness index, TRI) as a proxy for canyon structure, following the same approach already used for national-scale terrestrial resistance work in the existing pipeline.

(iii) Roads: OpenStreetMap road network, classified by type, motorway through unpaved track, consistent with the road resistance treatment already built into the existing resistance surface notebooks.

(iv) Species occurrence: GBIF records for verified focal species by functional group, aquatic, large herbivore, avian, supplemented by field survey observations where photo-confirmed.

5. Methods

(i) Build three single-factor resistance surfaces, hydrology only, terrain ruggedness only, roads only, each following the existing distance-decay approach already used for barriers and roads in the pipeline.

(ii) Build the combined resistance surface as currently structured, all factors together.

(iii) Run the circuit-theory current-flow solve, as implemented in the existing pure-Python pairwise workflow, on each single-factor surface and on the combined surface.

(iv) Layer ablation, compare the combined current map against versions with each factor held constant, hydrology removed, terrain removed, roads removed, in turn. The difference between the full model and each ablated version is that factor's estimated marginal contribution to overall connectivity.

(v) Identify pinch points, cells where current density is high in the combined model, and cross-reference against road/river/canyon intersections specifically, to answer the pinch-point question directly rather than only in aggregate.

6. Expected outputs

(i) A ranked estimate of each factor's relative contribution to landscape resistance in the study area.

(ii) A map of connectivity pinch points, prioritised by which factor or combination of factors is driving the constraint at each location.

(iii) A short methods report, written for reproducibility, GBIF pulls, resistance parameters, and the ablation results documented step by step.

7. Limitations

(i) The single-factor and ablation approach treats hydrology, terrain, and roads as independent, when in practice a road built along a valley floor is not independent of the terrain that put it there. Results should be read as relative weight under the model's assumptions, not as a claim of true causal independence.

(ii) Field-confirmed barrier data currently covers one site in detail, Pontão Manuel José, other barrier points still need coordinates before the hydrology layer reflects more than a single case.

(iii) Focal species occurrence data quality varies by group, the aquatic species list is drawn from a verified primary source, several terrestrial and invertebrate identifications from this fieldwork remain probable rather than confirmed and should be flagged as such in any published output.

8. Timeline

Aligned with the existing post-trip development schedule, W38 field reconciliation, W39 illustration and connectivity analysis, W42 final development. The single-factor and ablation modelling described here fits within the W39 window, since it depends on the resistance surface and circuit-theory notebooks already built, not on new fieldwork.

9. Relationship to the ArcGIS Story Maps

This proposal covers the scientific report only, single-factor resistance surfaces, ablation analysis, pinch-point mapping, written for reproducibility and aimed at a reader who already works with connectivity models. The five ArcGIS Story Maps sit alongside this as a separate, deliberately non-technical output, personal fieldwork experience told through site, species, and narrative, aimed at a general public with no GIS background. The two should stay distinct rather than merge, the report's ablation results can inform a Story Map's pinch-point visual, a finished map image rather than working data, but the Story Maps are not the place to walk a reader through the modelling itself. Keeping that separation is also what keeps the personal/institutional distinction clean, the Story Maps as personal experience, the report as an independent piece of analysis.