Story Map idea, realigned

Given the three plates now set (Movement — Vale Carapito, Water — Paul de Toirões, Connection — Ribeira do Mosteiro) and Almeida as the opening frame rather than the Water chapter itself, this realigns the earlier draft to match.

## Title ideas

(i) **Restoring the Côa: Movement, Water, Connection in a Rewilding Valley** — plain, does the job, tells a funder or a general reader exactly what they're getting.

(ii) **The Côa Runs Through It** — shorter, leans on the river as the spine connecting all three sites and three themes.

(iii) **Reading the Valley: A Rewilding Story from the Greater Côa** — foregrounds the fact that this is your own field interpretation, not just a project summary.

(iv) **Two Rivers, Two Stories: Connectivity and Return in the Côa Valley** — updated from the earlier "Between Two Dams" idea, now that the Porto/Douro comparison is a confirmed chapter rather than a maybe. Works well if the dam/barrier motif recurs visually across chapters and pays off at Porto.

## Contents, realigned

(i) **Opening frame — Three Centuries of a Frontier, Almeida.** The 1766 fortress map, a place built to control terrain and movement, pivoting to the same valley now managed for wildlife movement instead. Sets up the premise, not a connectivity chapter itself. The mouth-to-Almeida stretch and the rock art are already explored, this one is largely in hand.

(ii) **Water — Paul de Toirões.** No longer anchored on the Almeida weir alone, that data now folds in here as the flowing-water half of the longitudinal case, Pontão Manuel José as the small barrier, Ensecadeiras do Côa as the large one, closing on the verified fish list. Paul de Toirões adds the wetland half once you've been, standing water and marsh connectivity as the counterpoint. Your Survey123 barrier records and species table slot in directly, and this is also what feeds `04_resistance_surface_aquatic.ipynb`.

(iii) **Movement — Vale Carapito.** Horses and dung beetles as the functional-group anchor, the free-ranging cattle sighting near Almeida can still open this section as an early large-grazer note, verified Endangered Landscapes figures (23 Sorraia horses, 17 Tauros cattle, 656 ha under natural grazing) against your own ground-truth observations.

(iv) **Connection — Ribeira do Mosteiro.** Closing the three-plate structure, tying Water and Movement back together as one corridor rather than separate visits, natural home for the SOPHIA corridor-fragmentation argument.

(v) **Closing frame — Two Rivers, Two Stories, Porto, 20–21 August.** Replaces the earlier vague "reflection on rewilding as process." The Douro's history of damming and hydroelectric regulation against the Côa's civil-society fight to stop a dam and save the rock art, and the still-open Ensecadeiras do Côa removal case, connectivity as political choice rather than only ecological fact. Natural place for the QGIS/Omniscape connectivity modelling output too, if you want to fold that pipeline result in as a finished visual rather than keeping it fully separate.

## The open question, still open

Python connectivity pipeline or ArcGIS Story Map, or both, split by audience.

For the **Python/QGIS side** (scientific publication), the Côa data becomes methods material rather than narrative: barrier permeability classification maps directly onto resistance values for the Omniscape surface, and the species table is functional-group occurrence data feeding the model. Structure that output around reproducibility, GBIF pulls, resistance parameters, circuit theory results, written up as methods a reviewer can follow.

For **ArcGIS Story Map** (community share), the same data gets told the other way round, site first, species and barrier as illustration, not model input. The weir photo, the species you actually saw, the pontão's history as an old ford now half-submerged, that's the entry point for a reader with no GIS background. The Python side's modelling results can still appear here, as a finished map image, not as working data.

Practically, two clean exports from the same base: a tidy occurrence/barrier table for the Python pipeline, and a curated, captioned subset of the same sites and species for the story map, used differently depending on which output it's headed for.