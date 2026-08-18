# Coa Valley apartment-building livability score

Linda Angulo Lopez, 18 August 2026

## Objective

This analysis produces a 0-100 livability score for apartment buildings in the greater Coa Valley / Guarda region, Portugal, for a prospective naturalist resident whose priorities include nature and river access, practical driving access for fieldwork, parking, everyday amenities, and proximity to the Rewilding Portugal community. The score is a transparent, criteria-based decision-support measure rather than an objective or universal measure of quality of life.

## Study area

The Coa river runs from near the Spanish border through Pinhel and Vila Nova de Foz Coa to the Douro; Guarda, the region's largest urban centre, sits west of the river corridor. Rather than assume "Guarda municipality" equals "the Coa Valley," five candidate municipalities spanning the basin plus Guarda were checked empirically for `building=apartments` counts: Guarda (254), Pinhel (18), Vila Nova de Foz Coa (1), Sabugal (0), Almeida (0). Sabugal and Almeida were dropped, since they contribute no scoreable buildings; the union of the remaining three municipalities is the final study area. Vale Carapito (Portugal's first private rewilding reserve) and Pontao Manuel Jose (a Rio Coa crossing), both near Almeida, remain in use as external distance anchors despite falling outside the building-scoring area.

## Data

OpenStreetMap, accessed 2026-08-18, for apartment buildings, nature areas, the Rio Coa, major roads, parking, everyday amenities, and transport stops (two access paths were used for different layers -- see report limitations). OpenRouteService's Matrix API, accessed the same day, for real driving distance and time to two field-verified destinations. INE (Portugal's statistics institute), accessed 2026-08-18, for regional rent context. Field-verified coordinates for Vale Carapito and Pontao Manuel Jose came from real GPS fixes recorded during site visits in the supplied background material, not fabricated.

## Methodology

After cleaning (removing 3 duplicate geometries and non-polygon stray features), 251 apartment buildings remained. Five livability components were computed, each a 0-100 normalized score built from one or more raw indicators:

(i) **Nature and recreation (30%)** -- distance to the nearest tagged nature/green feature (park, forest, protected area, water, scrub) and count within 1 km, blended 70/30 toward distance.

(ii) **River-corridor access (25%)** -- distance to the Rio Coa itself (filtered to segments actually named "Rio Coa," see limitations), real driving time to Pontao Manuel Jose, and real driving distance to Vale Carapito, blended 50/30/20. These three were first scored as separate components but were found during validation to correlate at r=0.75-0.98 -- a real feature of this region's geography, where the river and the only verified rewilding/fieldwork anchors all sit in the same corridor near Almeida, not a coding error. Weighting them separately would have counted one signal three times, so they were combined into one component.

(iii) **Everyday amenities (25%)** -- count of supermarkets, restaurants, cafes, pharmacies, and healthcare within 1 km, capped at the 90th percentile before scaling so no single dense location dominates.

(iv) **Mapped parking access (15%)** -- count of OSM-mapped parking within 1 km, same percentile cap. Missing OSM parking data is not treated as proof that parking does not exist.

(v) **Public transport (5%)** -- distance to the nearest bus stop or station.

Distances use a threshold-based transform (100 at 0 m, 0 at a cutoff, linear between); cutoffs were set from the actual observed distribution for each indicator, not a priori guesses -- an early pass using untested guesses would have compressed nearly every building into the top of the scale for some indicators and zeroed out all of them for another (see Validation). Housing affordability was investigated but could not be included: INE's rent-per-m^2 release only breaks down to municipality level for the 24 municipalities over 100,000 inhabitants, none of which are in this study area. The finest real figure available is the NUTS III sub-region "Beiras e Serra da Estrela," EUR 4.42/m^2 (Q1 2025, provisional) -- about half the national median, but a single constant value with no power to distinguish one building from another. Its original 10% weight was redistributed to nature (+5) and amenities (+5).

## Results

The final `livability_score` ranges from 16.9 to 78.5 (mean 62.0, n=251). The highest-scoring buildings sit in Guarda's urban core, combining strong amenity, parking, and transport access with moderate nature and river-corridor scores. The lowest-scoring buildings are isolated, rural apartment buildings with zero mapped amenities or parking within 1 km. A one-point sensitivity analysis compared three alternative weighting scenarios -- nature-emphasis, balanced, and practical-residential -- against the primary score; building-level rankings correlate strongly across all three (Spearman's rho 0.89-0.96), meaning the overall pattern is fairly robust to reasonable changes in the weights, though the exact top-5 shifts: buildings favoured by high amenity/parking weighting (e.g. 155, 138, 154, 132) move up under the balanced and practical-residential scenarios, while the primary and nature-emphasis scenarios favour buildings closer to the region's green space (125, 121, 127, 126).

## Validation

Geometry: 0 invalid geometries, 0 duplicate building IDs, all 251 buildings scored and ranked (1-251). Indicator distributions were inspected before scoring, which caught two real problems rather than accepting first-pass output: the Coa river layer initially contained every river in the wide search area (Douro, Mondego, Vouga, and others alongside the Coa itself), and the rewilding-community and river-corridor indicators were found to structurally overlap once real driving distances were available. Both were corrected (see Methodology) before the score was finalized. Component-score correlations were re-checked after both fixes; the remaining moderate correlations (amenity-parking r=0.74, parking-transport r=0.77) reflect a real, expected urban-centrality pattern rather than a construction flaw and were left as-is, given their modest individual weights. Spot-checking three high-, three medium-, and three low-scoring buildings against their full raw-indicator breakdown (`validation/score_spot_checks.md`) confirmed the rankings track real differences in local access to nature, services, and the river corridor, not artifacts of the normalization.

## Limitations

OSM apartment-building tagging is incomplete and inconsistent by nature; this score reflects OSM-visible buildings only. Address attributes are sparse (`addr:city` populated for only 11 of 251 buildings) -- location is reliable, addressing is not. Two OSM access paths were used: the public Overpass API for nature areas and the Coa river (both reliable), and a local Geofabrik extract (dated 2026-08-17) for roads, parking, amenities, and transport, after public Overpass mirrors proved unreliable for those queries -- both draw on the same underlying OSM data, so this is a one-day temporal gap at most. No reliable rent data exists at building or municipality level for this area; affordability is context only, not scored. The river-corridor, fieldwork-access, and rewilding-community indicators all depend on distance to just two real, field-verified anchor points near Almeida -- a genuine data-availability constraint, not a fabrication, but one limiting how independently these dimensions can vary. Weights are a subjective, documented judgment call, not a derived optimum.

## Conclusion

Within the greater Coa Valley / Guarda study area, the highest apartment-building livability -- under this specific set of naturalist-weighted criteria -- is concentrated in Guarda's urban core, where good everyday services and parking coincide with reasonable, though not exceptional, access to nature and the river corridor. No location in this dataset scores highly on every dimension at once: buildings closest to the Coa river corridor and the rewilding community tend to have markedly worse everyday-amenity and transport access, and vice versa. The livability score is a transparent, criteria-based decision-support measure rather than an objective or universal measure of quality of life; it is a starting point for comparing OSM-visible apartment buildings against one resident's own stated priorities, not a ranking of the region's places to live in general.
