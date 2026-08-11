Story Map idea: 

Given the three narrative threads already set (Mouvement, Eau, Connexion) and Almeida as your base site, the first Côa weir data this  fits naturally as the opening chapter, the "Eau" thread starts right where you are.

## Title ideas:

(i) **Restoring the Côa: Movement, Water, Connection in a Rewilding Valley** — plain, does the job, tells a funder or a general reader exactly what they're getting.

(ii) **The Côa Runs Through It** — shorter, leans on the river as the spine connecting all three sites and three themes.

(iii) **Reading the Valley: A Rewilding Story from the Greater Côa** — foregrounds the fact that this is your own field interpretation, not just a project summary.

(iv) **Between Two Dams: Connectivity and Return in the Côa Valley** — more specific, works well if the weir/hydroelectric barrier data becomes a recurring visual motif across chapters.

## Contents, mapped onto your existing plan:

(i) **Opening: Almeida and the Côa.** Sets the landscape context, the border valley explaining itself, the battlefield history, and introduces Almeida as your observation base. The weir at Pontão Manuel José works well here as the first concrete site, low barrier, visible connectivity problem, easy entry point for a reader.

(ii) **Water.** Builds out from the weir and dam data you already have, longitudinal connectivity, fish species, the dammed pool as a case study in how infrastructure fragments a river even at small scale. This is where your Survey123 barrier records and species table slot in directly.

(iii) **Movement.** Vale Carapito material, horses and dung beetles as your functional-group anchor species, the free-ranging cattle sighting near Almeida could open this section too, since it's the same theme of large grazers shaping the landscape before you even reach Vale Carapito.

(iv) **Connection.** Ribeira do Mosteiro, closing the loop, tying the three sites back together as one connectivity network rather than three separate visits.

(v) **Closing.** Reflection on rewilding as process, not a fixed end state, natural place for the QGIS/Omniscape connectivity modelling if you decide to fold that pipeline output in rather than keeping it separate.

## The open question 
* Python connectivity pipeline or ArcGIS Instant Apps. 
Given the story map format itself, ArcGIS is the more natural fit for the narrative scroll, but nothing stops you from generating the resistance-surface maps in your existing pipeline and dropping them in as static figures and using the data in python or qgis for scientific publication

### changes what each output needs to do.

For the **Python/QGIS side** (scientific publication), the Côa weir data becomes methods material rather than narrative: the barrier permeability classification (fully blocking, partially crossable, easily crossable) maps directly onto resistance values for your Omniscape surface, and the species table is your functional-group occurrence data feeding the connectivity model. Worth structuring that output around reproducibility, the GBIF occurrence pulls, the resistance surface parameters, the circuit theory results, written up as methods a reviewer can follow, not as a story.

For **ArcGIS Story Map** (community share), the same underlying data gets told the other way round, site first, species and barrier as illustration, not as model input. The weir photo, the species you actually saw, the pontão's history as an old ford now half-submerged, that's the emotional/narrative entry point for someone with no GIS background. The connectivity modelling results from the Python side can still appear here, but as a finished map image or a simple before/after visual, not as the working data.

Practically, this means keeping two clean exports from the same base: a tidy occurrence/barrier table for the Python pipeline, and a curated, captioned subset of the same sites and species for the story map. The Pontão Manuel José record built out today already works for both, it just gets used differently depending on which output it's headed for.