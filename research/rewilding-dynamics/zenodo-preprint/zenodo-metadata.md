# Zenodo upload: values for the form

**Summary**: Field values for depositing the Rewilding Dynamics preprint (rabbit, wildcat, pond turtle) on Zenodo, and the checks to clear first.
**Last updated**: 2026-09-27 (PDF built; species focus changed from rabbit, wildcat, beaver to rabbit, wildcat, pond turtle)

---

**Deposited**: v0.1, 27 September 2026, DOI <https://doi.org/10.5281/zenodo.22997241>

## Files to upload

(i) `article.pdf` (main file, 15 pages, A4, built 2026-09-27). (ii) Optional: `article.md` as the source. (iii) Optional: the RIS reading list.

Rebuild the PDF after any edit to `article.md` (run from this folder, `coa` conda env):

```bash
/home/linda/anaconda3/envs/coa/bin/pandoc article.md -s --embed-resources --css article.css -o article.html
google-chrome --headless --disable-gpu --no-pdf-header-footer --print-to-pdf=article.pdf article.html
```

## Form fields

| Field | Value |
|---|---|
| Resource type | Publication / Preprint |
| Title | Rabbits, wildcats, pond turtles and a river that stayed: a synthesis and research agenda for trophic and hydrological rewilding in the Greater Côa Valley, Portugal |
| Creator | Angulo Lopez, Linda. Affiliation: Côa Connectivity Lab; Rewilding Academic Talent Program, Rewilding Portugal. ORCID: 0009-0009-5689-7148 |
| Publication date | date of upload |
| Description | the abstract below |
| Licence | CC BY 4.0 (text; the illustrations are not in this deposit, they are published separately under CC BY-NC 4.0 during Global Artivism Month) |
| Keywords | rewilding; trophic cascades; European rabbit; European wildcat; Mediterranean pond turtle; mesopredator release; prey switching; catchment hydrology; free-flowing rivers; rock art; field illustration; Portugal |
| Language | English |
| Version | v0.1 (preprint) |
| Additional notes | The literature search used Consensus, an AI search tool; drafting was assisted by Claude (Anthropic). Claims were checked against the cited papers by the author. Not peer reviewed. |

### Description (paste into the form)

Rewilding projects usually treat three questions separately: which predators to restore, how to recover prey, and how to restore rivers. In the Greater Côa Valley, northern Portugal, the three meet in three animals. The European rabbit (*Oryctolagus cuniculus*) is the keystone prey of the Iberian Peninsula and is now listed as Endangered in its native range. The European wildcat (*Felis silvestris*) depends on it. The Mediterranean pond turtle (*Mauremys leprosa*) links the pair to the river: an omnivore that comes through floods, drought and polluted water, provided summer pools hold water. The Côa itself is a largely free-flowing river, because a public campaign in the 1990s, "As gravuras não sabem nadar" (the engravings can't swim), stopped the dam that would have drowned its Palaeolithic rock art. This paper brings together about 45 references on (i) predator and mesopredator cascades, (ii) the rabbit as both endangered native and invasive alien, and (iii) rewilding, the water cycle and the pond turtle. It joins them into one chain of links for the valley, from grazing and fire through rabbits and wildcats to summer pools, pond turtles and river health. From that chain it sets out seven testable hypotheses. Each hypothesis is tied to a concrete step in the open Côa connectivity workflow (Angulo Lopez, 2026a): the rabbit joins the land group as a focal species, the pond turtle joins the water group, and the wildcat model is tested against rabbit habitat. The paper also describes an illustration method: new drawings of the rabbit, the wildcat and the pond turtle made in the fine-line style of the valley's Iron Age engravings, to be published during Global Artivism Month (1 November to 10 December 2026). None of the three animals appears in the known Côa rock-art record (Angulo Lopez, 2026b). Drawing them in the valley's own graphic language is a way to ask which animals the next chapter of this landscape will include.

## Related works

| Relation | Identifier | Type |
|---|---|---|
| References | Companion preprint, Movement, Water, Connection https://zenodo.org/doi/10.5281/zenodo.22979020 | Preprint |
| References | https://www.data.gouv.fr/datasets/coa-valley-eco-connectivity-v6 | Dataset |
| References | https://github.com/coa-connectivity-lab/eco-connectivity-workflow | Software |
| References | https://coa-connectivity-lab.github.io/global-artivism/?lang=es | Other (website) |

## Before uploading

(i) Markers still printed in the PDF (20 on 27 Sept): 8 `[verify]`, 8 `[check]`, 2 `[to draw]` (Figure 1), 1 `[choose]`, 1 `[add DOI once deposited]`. ORCID added. Decide for each: resolve, keep as an open question in the text, or delete. The `[verify]` in Section 2.2 describes the tagging method and can stay.
(ii) Section 7 (iii) now reads "Pond turtle survey were found for the Côa (Angulo Lopez, 2026a)", which conflicts with Table 1 row (vi) ("no pool survey found") and with the heading "survey before release". Confirm which is right.
(iii) Author contributions still says "All claims are to be checked ... before deposit". Change to past tense once done.
(iv) Delete the DRAFTING NOTE comment at the top of `article.md` (not printed in the PDF, but it ships if the source is uploaded).
(v) Deposit the companion preprint first, so this one can cite its DOI.
(vi) This folder is now public in the repository; only the Consensus notes (`notes/*.md`) stay git-ignored.
(vii) A Zenodo DOI is permanent. New versions can be added, but v0.1 stays public.
