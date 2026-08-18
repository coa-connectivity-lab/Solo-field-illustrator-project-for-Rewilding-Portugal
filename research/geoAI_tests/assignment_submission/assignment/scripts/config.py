"""
Configuration for the Coa Valley apartment-building livability analysis.

All study-area parameters, buffer distances, scoring thresholds, weights,
and output paths are centralised here so the rest of the pipeline has no
hard-coded values.
"""

import os
import socket
from pathlib import Path

import urllib3.util.connection as _urllib3_connection

# This sandbox's outbound IPv6 path is unreliable, and the Overpass API
# hosts resolve to IPv6 first; requests/urllib3 then intermittently hit
# "Connection refused" even though an IPv4 address for the same host works
# fine. Forcing IPv4-only DNS resolution for the whole process fixes this.
_urllib3_connection.allowed_gai_family = lambda: socket.AF_INET

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load secrets (e.g. ORS_API_KEY) from a local, untracked .env file rather
# than hard-coding them in this file. See assignment/.env (gitignored).
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _value = _line.partition("=")
            os.environ.setdefault(_key.strip(), _value.strip())

ORS_API_KEY = os.environ.get("ORS_API_KEY")
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_CACHE = PROJECT_ROOT / "data" / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_TABLES = OUTPUT_DIR / "tables"
OUTPUT_MAPS = OUTPUT_DIR / "maps"
VALIDATION_DIR = PROJECT_ROOT / "validation"

for d in [DATA_RAW, DATA_PROCESSED, DATA_CACHE, OUTPUT_DIR, OUTPUT_TABLES, OUTPUT_MAPS, VALIDATION_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# osmnx defaults its HTTP response cache to ./cache relative to the current
# working directory, which put it under scripts/ rather than the project's
# data/cache/ -- point it at the right place so raw/processed/output/cache
# stay logically separated as intended.
import osmnx as _ox

_ox.settings.cache_folder = str(DATA_CACHE / "osmnx")

GEOPACKAGE_PATH = OUTPUT_DIR / "coa_valley_livability.gpkg"

# ---------------------------------------------------------------------------
# Study area
# ---------------------------------------------------------------------------
# Candidate municipalities spanning the Coa river basin plus the regional hub
# (Guarda). Apartment-building counts per municipality are checked empirically
# in the data-acquisition step; municipalities with negligible counts may be
# dropped from the final study area, with the decision documented.
CANDIDATE_MUNICIPALITIES = [
    "Guarda, Portugal",
    "Sabugal, Portugal",
    "Pinhel, Portugal",
    "Almeida, Portugal",
    "Vila Nova de Foz Coa, Portugal",
]

# Final study area, narrowed from the candidates above after an empirical
# check of building=apartments counts per municipality (2026-08-18):
# Guarda 254, Pinhel 18, Vila Nova de Foz Coa 1, Sabugal 0, Almeida 0.
# Sabugal and Almeida are dropped from the apartment-building layer, since
# they contribute no scoreable buildings; their field-verified locations
# (Vale Carapito, Pontao Manuel Jose) remain in use as external distance
# anchors for the nature and rewilding-community indicators below.
STUDY_AREA_MUNICIPALITIES = [
    "Guarda, Portugal",
    "Pinhel, Portugal",
    "Vila Nova de Foz Coa, Portugal",
]

# Metric CRS for distance/area calculations: ETRS89 / Portugal TM06
METRIC_CRS = "EPSG:3763"
GEOGRAPHIC_CRS = "EPSG:4326"

# ---------------------------------------------------------------------------
# Buffer / threshold distances (metres), simple-distance-first per assignment
# ---------------------------------------------------------------------------
BUFFER_DISTANCES_M = {
    "walk_short": 500,
    "walk_long": 1000,
    "local": 3000,
    "regional": 5000,
    "wide": 10000,
}

# Distance beyond which a livability score for that indicator saturates at 0.
# These were originally set as a-priori guesses (see git history / plan), then
# recalibrated on 2026-08-18 against the actual observed distribution across
# the 251 apartment buildings (see validation/indicator_distributions.md),
# because the original guesses did not match reality:
#   - nature/major_road were far too loose (max observed 418m / 765m against
#     5000m / 3000m guesses), which would have compressed nearly every
#     building into the top of the 0-100 range with no real discrimination.
#   - rewilding_community was based on an assumed straight-line distance,
#     but the actual indicator uses real ORS driving distance to Vale
#     Carapito (36km-128km observed) -- the old 20km straight-line cutoff
#     would have scored every single building at 0.
# amenity and parking are intentionally absent: those two indicators are
# count-based (amenity_count_1km, parking_count_1km), not distance-based,
# and are normalized via COUNT_CAP_PERCENTILE instead.
DISTANCE_CUTOFFS_M = {
    "nature": 450,               # observed max 418m
    # river was recalibrated a second time: the first pass measured distance
    # to ANY river (waterway=river with no name filter picked up the Douro,
    # Mondego, Vouga and others alongside the Coa), giving a max of 3971m.
    # After filtering to segments actually named "Rio Coa" (see
    # acquire_indicator_layers.py), real distances are 2628m-52986m --
    # Guarda municipality, where most buildings are, is genuinely far from
    # the Coa itself. The old 4000m cutoff would have scored almost every
    # building at 0, which is what the validation spot-check caught.
    "river": 53000,
    "major_road": 800,            # observed max 765m
    "public_transport": 2500,     # observed p90 well under this; caps the long tail (max 11.3km) at 0
    "rewilding_community": 130000,  # real ORS driving distance; observed max 127.7km
}

# Fieldwork driving-time cutoff (seconds), same saturate-at-0 logic as the
# distance cutoffs above, calibrated against the observed 2595-6838s range.
FIELDWORK_DRIVE_TIME_CUTOFF_S = 7000

# Radius used for count-based indicators (amenities, parking)
COUNT_RADIUS_M = {
    "amenity": 1000,
    "parking": 1000,
    "park": 1000,
}

# Percentile cap applied to raw counts before min-max scaling, to stop one
# dense urban block from dominating the score (see assignment section 11).
COUNT_CAP_PERCENTILE = 90

# Sub-blends within a single component score, where more than one raw
# indicator feeds the same livability dimension (kept simple: at most two
# indicators per component, each with a clear rationale).
NATURE_SUBWEIGHTS = {"dist": 0.7, "count": 0.3}  # adjacency matters more than sheer count
FIELDWORK_ACCESS_SUBWEIGHTS = {"drive_time": 0.7, "major_road": 0.3}  # real driving time to field sites, plus general road proximity

# river_score, fieldwork_access_score, and rewilding_community_score were
# found (validate_results.py, 2026-08-18) to correlate at r=0.75-0.98 with
# each other -- not a coding artifact, but a real feature of this study
# area's geography: the actual Rio Coa, the only verified rewilding anchor
# (Vale Carapito), and the only verified fieldwork destination (Pontao
# Manuel Jose) all sit in the same corridor near Almeida. Three
# differently-named indicators were therefore measuring one underlying
# quantity -- distance from a building to the Coa valley corridor -- and
# weighting them separately would have counted that one signal three
# times. They are combined into one river_corridor_access_score (see
# compute_livability_score.py), with river weighted most heavily since it
# is the most direct, least sample-dependent of the three.
RIVER_CORRIDOR_SUBWEIGHTS = {"river": 0.5, "fieldwork_access": 0.3, "rewilding_community": 0.2}

# ---------------------------------------------------------------------------
# Weights (must sum to 100)
# ---------------------------------------------------------------------------
# affordability_score is NOT included: no rent data exists at building or
# municipality granularity for this study area (see NUTS3_REGION_RENT_EUR_PER_M2
# above for why). Its original 10% weight is redistributed 5/5 to nature and
# amenities, the two categories judged most likely to otherwise proxy for
# "practical, affordable living" in this rural context. If reliable
# building- or municipality-level rent data becomes available later, add an
# `affordability_score` column to the indicator table and reinstate a
# weight here (and in each scenario below) by taking it back out of nature
# and amenities.
LIVABILITY_WEIGHTS = {
    "nature_score": 30,
    "river_corridor_access_score": 25,
    "amenity_score": 25,
    "parking_score": 15,
    "transport_score": 5,
}
assert sum(LIVABILITY_WEIGHTS.values()) == 100, "Livability weights must sum to 100"

# Sensitivity-analysis scenarios: alternative weight sets, same indicators
# (affordability omitted from all three for the same reason as above).
SCENARIO_WEIGHTS = {
    "nature_emphasis": {
        "nature_score": 40,
        "river_corridor_access_score": 30,
        "amenity_score": 15,
        "parking_score": 10,
        "transport_score": 5,
    },
    "balanced": {
        "nature_score": 20,
        "river_corridor_access_score": 20,
        "amenity_score": 25,
        "parking_score": 20,
        "transport_score": 15,
    },
    "practical_residential": {
        "nature_score": 10,
        "river_corridor_access_score": 15,
        "amenity_score": 40,
        "parking_score": 30,
        "transport_score": 5,
    },
}
for name, weights in SCENARIO_WEIGHTS.items():
    assert sum(weights.values()) == 100, f"Scenario '{name}' weights must sum to 100"

# ---------------------------------------------------------------------------
# OSM tag definitions
# ---------------------------------------------------------------------------
APARTMENT_TAGS = {"building": "apartments"}

NATURE_TAGS = {
    "leisure": ["park", "nature_reserve", "garden"],
    "landuse": ["forest", "meadow", "recreation_ground"],
    "natural": ["wood", "water", "wetland", "scrub", "heath"],
    "boundary": ["protected_area", "national_park"],
}

RIVER_TAGS = {"waterway": "river"}

MAJOR_ROAD_TAGS = {"highway": ["primary", "secondary", "trunk", "motorway"]}

PARKING_TAGS = {"amenity": "parking"}

AMENITY_TAGS = {
    "shop": ["supermarket", "convenience", "bakery"],
    "amenity": ["restaurant", "cafe", "pharmacy", "hospital", "clinic", "doctors", "fuel"],
}

TRANSPORT_TAGS = {
    "highway": "bus_stop",
    "railway": "station",
}

# ---------------------------------------------------------------------------
# Housing affordability
# ---------------------------------------------------------------------------
# INE (Portugal's national statistics institute) publishes official median
# rent per m2 of new rental contracts ("Estatisticas de Rendas da Habitacao
# ao nivel local"), but the municipality-level breakdown in that release is
# restricted to the ~24 municipalities with over 100,000 inhabitants -- none
# of Guarda, Pinhel, or Vila Nova de Foz Coa qualify. The finest verifiable
# figure covering the study area is the NUTS III sub-region "Beiras e Serra
# da Estrela": median rent EUR 4.42/m2 in Q1 2025 (provisional), EUR 4.48/m2
# in Q4 2024 (source: INE, "Renda mediana de novos contratos de arrendamento
# de alojamentos familiares", tables downloaded 2026-08-18).
#
# That single regional figure is real and citable, but it is constant across
# the entire study area and so has no power to distinguish one apartment
# building from another -- it cannot serve as a per-building or even a
# per-municipality indicator. Per the assignment's own instructions, this is
# documented as a limitation rather than an invented affordability score:
# AFFORDABILITY_SCORE is left null in the output layer, and its 10% weight
# is redistributed to nature (+5) and everyday amenities (+5) in
# LIVABILITY_WEIGHTS below. The regional rent figure is reported as context
# in the written report only.
NUTS3_REGION_RENT_EUR_PER_M2 = {
    "region": "Beiras e Serra da Estrela",
    "q1_2025_provisional": 4.42,
    "q4_2024": 4.48,
    "source": "INE, Renda mediana de novos contratos de arrendamento de alojamentos familiares",
    "accessed": "2026-08-18",
}

# Field-verified rewilding/scientific community anchor point(s).
# Sourced from field-trip notes supplied with the assignment (not fabricated):
# Vale Carapito, confirmed on the Rewilding Portugal website as Portugal's
# first private rewilding protected area.
REWILDING_COMMUNITY_POINTS = [
    {"name": "Vale Carapito (Rewilding Portugal reserve)", "lat": 40.6562341, "lon": -6.9092832},
]

# Representative field-trip / fieldwork destination(s) for driving-
# accessibility scoring, drawn from the same field-verified notes.
#
# Vale Carapito is deliberately NOT included here even though it is a real
# fieldwork site: it is the sole REWILDING_COMMUNITY_POINTS anchor above, and
# an early version of this pipeline used it in both FIELDWORK_DESTINATIONS
# and REWILDING_COMMUNITY_POINTS, which made fieldwork_access_score and
# rewilding_community_score structurally near-duplicates (both driven by
# distance to the same point; observed correlation r=0.83, see
# validation/). Keeping the two indicators built from different points is
# what makes "regional driving access in general" and "proximity to the
# rewilding community specifically" genuinely distinct livability
# dimensions, as the assignment intends them to be, rather than the same
# number counted twice under two names.
FIELDWORK_DESTINATIONS = [
    {"name": "Pontao Manuel Jose (Rio Coa, Almeida)", "lat": 40.6787318, "lon": -6.9213772},
]
