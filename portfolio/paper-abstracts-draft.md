# Draft paper abstracts
Linda Angulo Lopez, 22 August 2026

Seven candidate papers drawn from the Greater Côa Valley eco-connectivity pipeline (v1–v4) and its six companion desk studies. Each is a draft abstract only — title and venue are suggestions, not commitments, and every abstract below inherits the underlying work's own stated limitations (noted in brackets where the claim is genuinely open rather than settled). Order is roughly pipeline-methods first, then the comparative/policy papers built on top of it.

---

## 1. A reproducible, pure-Python connectivity pipeline for a data-sparse rewilding landscape

**Suggested venue:** *Methods in Ecology and Evolution*, *Conservation Science and Practice*, or similar applied-methods venue.

**Abstract.** Landscape-connectivity modelling for conservation planning typically relies on Circuitscape/Omniscape.jl, which requires a Julia runtime uncommon in conservation-NGO computing environments, and on species-occurrence data that is often sparse or absent for actively rewilding sites. We present a fully Python-based circuit-theory pipeline (scipy.sparse pairwise current-flow solving) applied to the Greater Côa Valley, Portugal, a 1,023,036 ha rewilding landscape with no published occurrence-quality boundary of its own. The pipeline combines Random Forest suitability models trained on GBIF occurrence data (using a deliberately permissive 30 km coordinate-uncertainty threshold to retain usable sample sizes) with resistance surfaces for three functional groups (terrestrial, aquatic, avian) following Prima et al. (2024)'s framework. We extend the base method with two field-evidence-derived resistance penalties absent from the original framework: a distance-decayed barrier penalty built from citizen-science Survey123 field observations (fences, dams, roads; validated by direction-of-effect, e.g. "fully blocking" barriers show measurably higher local resistance than "easily crossable" ones), and an area-fill penalty for UNESCO World Heritage protected landscapes that are ecologically poor matrix and legally unavailable for conservation land-use conversion. We report the pipeline's own validation limitations candidly, including RF accuracy metrics that are not out-of-sample validation, run-to-run stochasticity from an undocumented random seed, and a resistance-grid resampling step that dilutes fine-scale field-evidence effects. We argue this stack is a practically reproducible template for resource-constrained conservation organisations rather than a methodological advance over Circuitscape itself.

**Keywords:** landscape connectivity, circuit theory, resistance surface, citizen science, rewilding, Portugal, reproducibility

---

## 2. Legal geographies of ecological water rights: South Africa's statutory Reserve and the absence of a Portuguese or EU equivalent

**Suggested venue:** *Environmental Politics*, *Journal of Environmental Law*, or a political-ecology venue.

**Abstract.** South Africa's National Water Act 1998 establishes "the Reserve," a legally binding minimum water allocation prioritising basic human needs and ecosystem health ahead of all other water-use categories, enacted explicitly to redress apartheid-era water inequity. This paper asks whether any comparable statutory floor exists in Portuguese or EU law, and finds that it does not: Natura 2000 designation and the EU Water Framework Directive are descriptive protective regimes, not allocation guarantees, and the only comparable rights-of-nature instruments at EU level are an unadopted 2017 draft directive and an ongoing 2026 European Citizens' Initiative that has not yet reached legislative force. We use this legal asymmetry as an explanatory frame for a concrete case: the near-absence of large wildlife in the Greater Côa Valley, Portugal, today, arguing that twentieth-century land-use intensification, EU Common Agricultural Policy-driven land abandonment, and historical predator persecution proceeded without any legal mechanism prioritising ecological water or land needs, leaving voluntary private land purchase (the current rewilding model in the valley) as the only mechanism doing what a statutory Reserve-equivalent might otherwise guarantee. We are careful to distinguish South Africa's Reserve, a minimum-allocation mechanism, from genuine rights-of-nature/legal-personhood frameworks such as Ecuador's constitutional provisions or the Whanganui River settlement, and flag that no source in our review directly compares the Reserve to personhood-based regimes, an open question for further legal-comparative work.

**Keywords:** rights of nature, water law, National Water Act, apartheid, EU environmental law, rewilding, legal geography

---

## 3. When conservation follows dispossession, not the reverse: comparing resistance to wildlife recovery in post-apartheid South Africa and rural Portugal

**Suggested venue:** *Conservation and Society*, *Human Dimensions of Wildlife*, or an environmental-sociology venue.

**Abstract.** Public resistance to conservation is often treated as a single phenomenon, but its sources differ sharply by historical context. We compare three distinct forms of resistance to wildlife recovery in the Greater Côa Valley, Portugal, and the Greater Kruger/Limpopo landscape, South Africa: resistance to conservation policy itself (Portuguese wolf-livestock conflict and compensation disputes, versus South African fence-removal and cross-boundary livestock-loss conflict); resistance rooted in historical dispossession (the well-documented 1969 forced removal and 1998 restitution of the Makuleke community from what became Kruger National Park, a paradigm case of fortress-conservation displacement); and everyday coexistence tolerance (Portugal's 337 active hunting concessions and documented attitude-survey findings that livestock owners, not hunters, are the most wolf-hostile group, against South Africa's disputed trophy-hunting/photographic-tourism revenue split and community benefit-sharing rates). Critically, we find no honest Portuguese parallel to the second category: the Côa Valley's depopulation was economically driven emigration that preceded conservation interest by decades, the reverse causal sequence from Kruger's conservation-driven removal. We argue this asymmetry, not a shared "resistance to conservation" narrative, is the more useful comparative finding, and caution against importing South Africa's fortress-conservation framing into contexts, like rural Portugal, where it does not empirically apply.

**Keywords:** human-wildlife conflict, fortress conservation, forced removal, rewilding, wolf conservation, South Africa, Portugal

---

## 4. From hunting-zone cadastre to safari economics: a land-tenure feasibility assessment for rewilding-tourism upscaling

**Suggested venue:** *Land Use Policy*, *Biological Conservation*, or a conservation-economics venue.

**Abstract.** Advocates of European rewilding frequently invoke southern African transfrontier conservation areas as an aspirational model, but the land-tenure preconditions for that model are rarely quantified against a specific European case. We compute, from the Greater Côa Valley's own cadastral and protected-area data, the actual scale barriers to Limpopo-style safari-tourism upscaling: 337 hunting-zone parcels covering 663,158 ha (mean parcel size 1,968 ha, well under literature-cited minimum viable ranges for large-carnivore reintroduction) under active, non-purchasable licence; a private-reserve layer showing a substantial data-quality undercount against published figures, a caution for any land-tenure GIS work in the region; two hard legal exclusions from UNESCO World Heritage protection status (a working wine-terrace landscape and an archaeological rock-art core) totalling 7,184 ha once intersected with the actual study-area boundary, an order of magnitude smaller than the raw published heritage-site area once the non-overlapping portion is excluded; and a resulting achievable ceiling of roughly 10% of the Greater Limpopo Transfrontier Conservation Area's scale, against land actually held today of under 0.01%, since a land-purchase-only acquisition model cannot replicate the fence-removal-between-existing-landowners mechanism that scaled the southern African case. We present this as a feasibility ceiling under current institutional constraints, not a forecast, and argue that cadastral-resolution land-tenure analysis, not headline hectare comparisons, is the appropriate unit of comparison for cross-continental rewilding-scale claims.

**Keywords:** land tenure, safari tourism, transfrontier conservation, rewilding, land fragmentation, ecotourism economics

---

## 5. The hydropower "safety valve" hypothesis: an open question in the political economy of Portugal's 1996 Foz Côa dam cancellation

**Suggested venue:** *Environmental History*, *Water History*, or a political-ecology/energy-history venue. Likely framed as a research note or perspective piece rather than a full empirical paper, given the evidentiary gap noted below.

**Abstract.** Portugal's 1996 cancellation of the Foz Côa hydroelectric dam, prompted by the discovery of Palaeolithic rock engravings, is conventionally narrated as a heritage-versus-development conflict resolved on cultural-value grounds. We document an underexamined structural condition of that decision: by 1991, when the EDP-IPPAR agreement authorising Foz Côa's construction was signed, the Douro River's major hydroelectric cascade (six dams, roughly 1,680 MW installed capacity, later 1,800 MW with the addition of Crestuma-Lever) had already been fully operational for close to a decade. We pose, without claiming to resolve, a hydropower "safety valve" hypothesis: that the Douro cascade's pre-existing capacity gave Portuguese energy policy room to cancel a comparatively small additional contribution without a real supply-adequacy cost, in a counterfactual sense that a Foz Côa proposed in the absence of that capacity might not have been. We searched contemporaneous energy-policy sources and the existing academic literature on the Foz Côa case (which treats it as a values-conflict resolved via multi-criteria weighing, not an energy-adequacy calculation) and found no direct evidence either confirming or ruling out this hypothesis. We present the verified capacity and timeline data as a foundation for future archival or oral-history research, explicitly flagging that establishing actual causation for a single historical political decision is beyond what desk research alone can demonstrate.

**Keywords:** dam removal, political ecology, energy policy, cultural heritage conservation, Douro, Foz Côa, counterfactual history

---

## 6. Siting-conditional renewable advocacy in practice: an integrated infrastructure proposal for a small-scale rewilding landscape

**Suggested venue:** *Energy Policy*, *Renewable and Sustainable Energy Reviews* (policy/case-study section), or *Ecological Economics*.

**Abstract.** Conservation organisations opposing individual renewable-energy siting decisions are frequently characterised, by proponents and critics alike, as broadly anti-renewable. We use Rewilding Portugal's own documented, siting-conditional opposition to the SOPHIA solar project (explicitly not a rejection of solar energy, but a demand for already-artificialised siting and a "Nature-based Energy Transition programme") as a case study to ask whether this position can be generalised into constructive proposals rather than case-by-case reaction. We present a concrete, site-specific integrated-infrastructure proposal for the Greater Côa Valley combining two revenue-generating uses of already-disturbed land: agrivoltaic-derived solar canopies over existing reserve access roads (order-of-magnitude illustrative capacity 0.3–0.6 MW and €30,000–80,000/year per site, adapted from established agrivoltaic engineering rather than a proven road-canopy precedent) and small-scale photographic-tourism lodges modelled on, but scaled honestly down from, the Timbavati Private Nature Reserve's conservation-levy funding mechanism (illustrative €80,000–225,000/year per site, given Côa reserves at roughly 1–2% of Timbavati's scale). We situate this proposal against Portugal's own live national renewable-siting policy transposition (the 2026 "Mapa Verde" acceleration-zone framework, which already excludes Natura 2000 areas), arguing that siting-conditional advocacy has more traction when paired with a constructive land-use alternative than when left as opposition alone, while being explicit that our economic figures are illustrative estimates, not an engineering-ready feasibility study.

**Keywords:** renewable energy siting, agrivoltaics, ecotourism, conservation finance, land-use policy, rewilding

---

## 7. A multi-layer field-survey and heritage-protection geodatabase for the Greater Côa Valley rewilding landscape

**Suggested venue:** *Data in Brief*, *Scientific Data*, or a GIS/data-descriptor venue — a companion data paper to no. 1 above.

**Abstract.** We describe a compiled, open geospatial dataset supporting eco-connectivity analysis in the Greater Côa Valley, Portugal: a citizen-science Survey123 field-observation layer (22 site visits, 26 melted species observations, 25 melted barrier observations with permeability assessments), reconciled against an earlier, less complete export of the same underlying form to demonstrate a repeatable schema-evolution pattern for growing citizen-science datasets; and a UNESCO World Heritage protected-landscape layer for two sites overlapping the study area (the Alto Douro Wine Region and the Prehistoric Rock Art Sites of the Côa Valley), sourced from Portugal's official cultural-heritage geoportal after two more commonly used sources (UNESCO's own boundary data and the World Database on Protected Areas) proved unusable for these specific, culturally rather than naturally classified sites, a sourcing dead-end worth documenting for other researchers attempting the same lookup. We report data-quality findings arising from the compilation process itself, including a confirmed undercount in an existing private-reserve layer against independently published figures, and describe the melting/validation logic used to separate genuine physical barriers from a small number of misclassified fire-disturbance and stray-annotation records in the raw survey export. All layers are released in a common CRS (EPSG:3035) alongside the scripts used to build them.

**Keywords:** geospatial data, citizen science, Survey123, UNESCO World Heritage, protected areas, data descriptor, Portugal
