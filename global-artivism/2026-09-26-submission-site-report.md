# Global Artivism Month 2026: submission website

**Summary**: What was built on 26 September 2026 for the coa-connectivity-lab entry to Global Artivism Month (1 November to 10 December 2026), why, and what is still open.
**Last updated**: 2026-09-26

---

## Context

coa-connectivity-lab registered for Global Artivism Month on the movement's participation form and chose "Share my art". The form asks for a title, a credit line, a one or two line description and a link to the work. The Côa call plan in [global-artivism-call.md](global-artivism-call.md) also needed a public page. One website now does both jobs.

- Live site: https://coa-connectivity-lab.github.io/global-artivism/
- Repository (public): https://github.com/coa-connectivity-lab/global-artivism
- Local copy: `/home/linda/Documents/myData/global-artivism/`

The site sits in its own public repository because GitHub Pages is free only for public repositories, and this repository is private. Nothing in this repository was moved or changed apart from this report.

## What the site contains

The site is a single self-contained HTML page with no build step, in four languages: English, Portuguese, Spanish and French. It chooses the visitor's browser language, and a direct link can force one, for example `?lang=es`.

(i) **The work.** Title, credit, year and place, medium (illustration and digital GIS maps) and a short statement of what the work is about.

(ii) **Three paired panels.** Each of the project's three stories, Movement, Water and Connection, shows an illustration slot next to a connectivity map:

| Story | Illustration slot | Map (Omniscape output, v6 bundle) |
|---|---|---|
| Movement | Herbivores at Vale Carapito | `land_normalized_current.tif` (wolf, wildcat, red deer) |
| Water | Paul de Toirões wetland | `water_normalized_current.tif` |
| Connection | Côa gorge and Penascosa rock art | `multispecies_mean_connectivity.tif` |

The illustration slots are placeholders because `illustrations/final-plates/` is still empty. Dropping a scan into the site's `img/` folder with the right name (`movement.jpg`, `water.jpg`, `connection.jpg`, `sketch-01.jpg` to `sketch-12.jpg`) replaces the placeholder with no HTML change.

(iii) **Field-site map.** An interactive Leaflet map of the 20 sites visited in August 2026.

(iv) **Why this work.** A short text on why drawing and modelling read the same valley in different ways. It credits the Indigenous and community-led origin of "safe and just" before the Earth Commission work, following [the citation correction](../field-trips/deskStudy/safe-and-just-indigenous-science-earth-system-justice.md).

(v) **The Côa call.** The three ways to take part (witness, contribute one page, co-create), the timeline from 6 October to 10 December, and a link to GitHub Discussions on the site repository.

(vi) **Rights and consent.** Contributors keep their rights, work is shared under CC BY-NC 4.0, the zine is opt-in, and nobody or no sensitive species is put at risk. A line states plainly that this is a locally organised action, not run by the Global Artivism team.

## How the maps were made

The analytical PNGs in `research/eco-connectivity/output/maps/` have projected-metre axes and are built for a notebook, not for a gallery. The script `scripts/render_maps.py` in the site repository redraws the three maps from the v6 rasters with no axes. It adds the Côa river, a 10 km scale bar and a north arrow. The script runs in the existing `coa` conda environment and installs nothing:

```bash
conda run -n coa python scripts/render_maps.py
```

The input is the unzipped v6 bundle at `/home/linda/Documents/myData/coa-eco-connectivity-data-v6/`, the same data published on [data.gouv.fr](https://www.data.gouv.fr/datasets/coa-valley-eco-connectivity-v6) under Licence Ouverte 2.0. The underlying sources are credited in the page footer.

## Data and privacy decisions

(i) **No species locations.** The field-site map uses only the `visited_sites` layer of `field_observations.gpkg`. Species and barrier points are left out, because exact wildcat and otter locations are sensitive.

(ii) **Only non-sensitive sites inside the study area.** Sites flagged `sensitive` are dropped, and so is anything outside the study area (the Camargue, Limpopo and Fontainebleau comparisons, and the Porto sites), leaving 20 sites.

(iii) **No personal email.** The call does not publish a personal address. A contact for people without a GitHub account is announced as coming before 6 October.

(iv) **No third-party images.** The two Google Maps screenshots in `field-trips/` (`Study_Site.png`, `National_Parks.png`) are not used.

(v) **Text only for the Global Artivism name.** The Global Artivism logo is not used until the Terms and Conditions on name and identity use have been checked.

## Values for the participation form

| Field | Value |
|---|---|
| Title of the work | Movement, Water, Connection: field notes and maps from the Côa Valley |
| Credit line | Linda Angulo Lopez, coa-connectivity-lab |
| Year and place | 2026, Greater Côa Valley, Portugal |
| What the work is about | Where can a wolf, an otter or a seed still move through a valley shaped by dams, roads and fire? The drawings answer from the ground, the maps from the data. |
| Medium | Illustration or painting; Other: digital GIS maps |
| Link | https://coa-connectivity-lab.github.io/global-artivism/ |

## Checks done

- All four languages have the same 54 text blocks, and there are no em dashes in the text.
- The page renders at desktop and 360 to 375 px phone widths with no horizontal scroll.
- The GitHub Pages build reports `built`, and the page, map images and Discussions link return HTTP 200.

## Open items

| Item | Deadline |
|---|---|
| Add a contact for people without a GitHub account | before sign-up opens on 6 October |
| Review the Portuguese, Spanish and French drafts (English is the reference text) | before 6 October |
| Read the Terms and Conditions, then decide on the logo | before 6 October |
| Scan the plates and sketches into the site's `img/` folder, with a visible credit on any image not made by Linda | as plates are finished |
| Fill in and submit the "Share my art" block of the form with the values above | before the month opens on 1 November |

Which of the three stories will be ready first, and should it lead the page when the month opens?
