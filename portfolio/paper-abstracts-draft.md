# Draft paper abstracts
Linda Angulo Lopez, 22 August 2026, updated 23 August 2026

Eleven candidate papers drawn from the Greater Côa Valley eco-connectivity pipeline (v1–v5) and its eleven companion desk studies. Each is a draft abstract only — title and venue are suggestions, not commitments, and every abstract below inherits the underlying work's own stated limitations (noted in brackets where the claim is genuinely open rather than settled). Order is roughly pipeline-methods first, then the comparative/policy papers built on top of it. Abstracts 8–11 are new, drawn from v5's corrections and closing sections; abstracts 1–7 are unchanged from the original draft.

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

---

## 8. Whose framework? A case study in correcting epistemic attribution within applied conservation science

**Suggested venue:** An environmental social-science or science-and-technology-studies venue, or *Environmental Science & Policy*.

**Abstract.** Applied conservation science routinely borrows normative frameworks from adjacent fields without auditing their intellectual lineage. We document a concrete instance from our own work: an eco-connectivity notebook for the Greater Côa Valley initially credited its "safe and just" framing to a 2012 mainstream sustainability-economics model, then corrected that attribution across two rounds of revision once the framing's actual sources were properly traced, first to the Earth Commission's 2023 justice-integrated planetary-boundaries work, then further back to Indigenous Science and community-led climate justice movements that have held the underlying idea, living within ecological limits while upholding justice and right relationship with the land, for far longer than any Western academic paper. We present this correction itself as the case study: what it took to notice the misattribution, what sources correctly establish the idea's actual lineage, and what changes, and what does not, when a conservation-science document's normative framing is corrected rather than left standing on a convenient but wrong citation. We are explicit that this is a reflexive methods contribution, not a claim to have resolved the underlying epistemic-justice literature's own open questions about how Earth-system science should relate to Indigenous knowledge systems it does not originate from.

**Keywords:** epistemic justice, Indigenous science, planetary boundaries, reflexivity, conservation science, citation practice

---

## 9. Ocean currents as the physical infrastructure of empire: land-to-sea connectivity between Portugal and its former colonies

**Suggested venue:** *Environmental History*, *Water History*, or a historical-geography venue.

**Abstract.** Portugal's colonial reach into Brazil, Angola, and Mozambique is conventionally narrated through administrative, linguistic, and economic history. We argue the physical mechanism deserves equal billing: the North and South Atlantic Gyres and the Agulhas Current were not a backdrop to Portuguese expansion, they were its literal, load-bearing infrastructure. The *volta do mar* navigational technique used the North Atlantic Gyre's clockwise circulation to make the West African route viable at all; Cabral's 1500 landfall in Brazil was a direct consequence of South Atlantic Gyre currents and trade winds carried out on the same logic, not chance; the Benguela Current forced a wide Atlantic detour past Angola that is itself the reason Cabral's route crossed the ocean it did; and the Agulhas Current carried ships on to Mozambique and India. We further argue this connectivity did not end with empire: the Benguela Current is today a major upwelling fishery undergoing documented climate-driven warming with direct consequences for Angolan food security, the Agulhas Current sustains coral-reef biodiversity in Mozambique's Quirimbas Archipelago, and the Portuguese Current carries microplastics along Portugal's own coast today. We frame this as ecological connectivity, the same conceptual tool used elsewhere in this research programme's circuit-theory modelling, applied at ocean-basin rather than landscape scale.

**Keywords:** ocean currents, colonial history, environmental history, Age of Discovery, Benguela Current, Agulhas Current, ecological connectivity

---

## 10. Colonial extraction, community resistance, and civil war: three divergent ecological policy trajectories in Brazil, Mozambique, and Angola

**Suggested venue:** *Journal of Political Ecology*, *World Development*, or a postcolonial-studies venue.

**Abstract.** We compare colonial-era environmental policy and its post-independence trajectory across three former Portuguese colonies, finding three genuinely different stories rather than one shared "colonial legacy" narrative. Brazil's coastal Atlantic Forest was cleared from first contact while its Amazon interior remained largely unsettled through the colonial period, a split later addressed, imperfectly but measurably, by strong post-independence state institutions culminating in a documented 11% year-on-year fall in Amazon deforestation as of the most recent reporting. Mozambique's colonial extraction pattern is being actively reproduced in the present by ProSavana, a Brazil–Japan–Mozambique agribusiness project threatening an estimated four million small-scale farmers, constrained not by state policy but by community-led resistance, Mozambique's own Justiça Ambiental and UNAC peasants' union, joined by Brazil's Landless Workers' Movement (MST), a direct present-day instance of cross-border, community-led environmental justice organising. Angola's late-colonial conservation infrastructure, a 1911 hunting-licence conservation fund expanding into protected parks by the 1930s and 1970s, collapsed entirely during the post-independence civil war, with the resulting governance vacuum filled by diamond and oil extraction continuing colonial logics under new ownership. We argue the common thread across all three is not the colonial administrations' own environmental record but the record of who resisted, rebuilt, or is still contesting a different relationship with the land, and that this standpoint, not a state-to-state policy comparison, is the more honest unit of analysis.

**Keywords:** postcolonial political ecology, Brazil, Mozambique, Angola, environmental justice, ProSavana, land grabbing

---

## 11. Remote work, AI, and the future conservation workforce: a prospective assessment for a small-scale European rewilding landscape

**Suggested venue:** A conservation-careers or future-of-work venue, or *People and Nature*.

**Abstract.** Rural rewilding initiatives face a persistent staffing constraint distinct from the land-tenure and funding constraints more commonly studied: low local population density limits the pool of nearby skilled labour and volunteers. We assess whether two recent structural shifts, post-COVID normalisation of remote work and AI tools lowering the effort barrier for remote-contributable conservation-support tasks (GIS analysis, translation, communications, grant writing), constitute a genuine emerging opportunity for a landscape like Portugal's Greater Côa Valley. We document three real, already-existing pieces of infrastructure this could draw on: Portugal's D8 Digital Nomad Visa, in place since 2022 with over 2,600 visas issued by 2024; Madeira's government-backed Ponta do Sol "Digital Nomad Village" as a working precedent for purpose-built remote-work-plus-place infrastructure; and southern Africa's FGASA/EcoTraining field-guide and reserve-manager training pipeline, internationally recognised but, per Rewilding Europe's own published assessment, translating into European roles that skew toward conservation management, policy, and communications rather than direct field-ranger work. We candidly report finding no evidence that this pipeline is yet operating at scale for the Côa Valley specifically, beyond one documented case, the lead author's own position in a structured academic-talent programme supporting the same initiative. We present this as a well-grounded prospective opportunity worth naming plainly, not a documented trend, and close on the observation that workforce capacity, unlike land, is not fenced, licensed, or bound by inheritance.

**Keywords:** future of work, remote work, artificial intelligence, conservation workforce, digital nomad visa, rewilding, volunteer tourism
