"""
config.py
─────────
Paths, CRS, and the Guarda-origin / rewilding-site destinations for the
visitor off-road/4x4 accessibility analysis (companion to the notebook v6
"Where could a naturalist live, and how do visitors reach the rewilding
sites?" section). This is about ecotourism access TO the rewilding sites,
not Linda's own field-visit history — see acquire_offroad_routes.py and
compute_guarda_access.py.

Conda environment: `coa`. Standalone study, same reasoning as
research/fontainebleau-comparison/, research/camargue-comparison/, and
research/limpopo-mine-restoration/ — not part of the eco-connectivity
resistance/suitability pipeline.
"""

import os
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent.parent  # research/guarda-rewilding-access/
DATA_PROCESSED = THIS_DIR / "data" / "processed"
OUTPUT_MAPS = THIS_DIR / "output" / "maps"
OUTPUT_TABLES = THIS_DIR / "output" / "tables"
for _d in (DATA_PROCESSED, OUTPUT_MAPS, OUTPUT_TABLES):
    _d.mkdir(parents=True, exist_ok=True)

ROUTES_GPKG = DATA_PROCESSED / "offroad_routes.gpkg"
ACCESS_TABLE_CSV = OUTPUT_TABLES / "guarda_access.csv"

# ── CRS ──────────────────────────────────────────────────────────────────
CRS_DISPLAY = "EPSG:4326"
# ETRS89 / Portugal TM06 — matches the livability assignment's own METRIC_CRS
# (/home/linda/Documents/myData/agentic_coding_geospatial/assignment/scripts/
# config.py), since this analysis extends that study's ORS pattern and covers
# the same Guarda/Côa area. Deliberately not EPSG:3035 (eco-connectivity's own
# continent-wide CRS) — a national-scale Portugal study is better served by
# Portugal's own official projected CRS, same reasoning
# research/fontainebleau-comparison/scripts/config.py gives for using
# France's Lambert-93 instead of EPSG:3035.
CRS_METRIC = "EPSG:3763"

# ── OpenRouteService (reused pattern) ───────────────────────────────────
# Loaded from the livability assignment's own .env (not duplicated into this
# repo) — same key, same reasoning as
# /home/linda/Documents/myData/agentic_coding_geospatial/assignment/scripts/
# config.py's own loader below.
_LIVABILITY_ENV = Path("/home/linda/Documents/myData/agentic_coding_geospatial/assignment/.env")
if _LIVABILITY_ENV.exists():
    for _line in _LIVABILITY_ENV.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _value = _line.partition("=")
            os.environ.setdefault(_key.strip(), _value.strip())
ORS_API_KEY = os.environ.get("ORS_API_KEY")
ORS_MATRIX_URL = "https://api.openrouteservice.org/v2/matrix/driving-car"
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

# ── Overpass (reused retry-with-backoff pattern) ────────────────────────
# Same retry logic as research/fontainebleau-comparison/scripts/
# osm_utils.py's overpass_post() — copied rather than cross-imported, since
# that module's own `import config` would otherwise collide with this
# project's own config.py of the same name if both were on sys.path at once.
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "linda-guarda-rewilding-access/1.0"

# ── Origin ───────────────────────────────────────────────────────────────
# Guarda city centre, NOT osmnx's own geocode_to_gdf()/geocode() result for
# "Guarda, Portugal" — that returned two different, wrong points (a
# municipality-boundary centroid at 40.641,-7.230, and a geocode point at
# 40.705,-7.195, both well off the real city). Verified instead against
# independent sources (geodatos.net, latitude.to), which agree at
# 40.5373,-7.2658 — the historic city centre, Portugal's highest-elevation
# city (1,056 m).
ORIGIN = {"name": "Guarda (city centre)", "lat": 40.5373, "lon": -7.2658}

# ── Destinations: the 3 real, already-geolocated rewilding sites ───────
# Pulled from research/eco-connectivity/data/processed/field_observations.gpkg
# ::visited_sites (post Phase-0 refresh, non-sensitive, in_study_area=True
# for all three) — real field GPS, not estimated.
#
# Vale Carapito reconciliation: the external livability assignment's own
# config.py (/home/linda/Documents/myData/agentic_coding_geospatial/
# assignment/scripts/config.py::REWILDING_COMMUNITY_POINTS) gives Vale
# Carapito as (40.6562341, -6.9092832) — roughly 20 km north of the point
# used here. Checked against an independent source (birdingplaces.eu, which
# publishes its own coordinate for the site): 40.473673722152,
# -6.9385972051161 — within ~2 km of this project's own field-recorded
# point below, not the livability assignment's. The livability assignment's
# point looks like a geocoding error; this analysis uses the field-verified
# point and does NOT silently adopt the mismatched one. Worth flagging back
# to the livability assignment separately — out of scope to fix that
# external repo from here.
DESTINATIONS = [
    {"name": "Faia Brava", "lat": 40.905417, "lon": -7.095984},
    {"name": "Vale Carapito", "lat": 40.483100, "lon": -6.950300},
    {"name": "Ermo das Águias", "lat": 40.785694, "lon": -7.010354},
]

# Routing corridor for the off-road/track Overpass query: a generous bbox
# covering Guarda and all three destinations, with margin (lon_min, lat_min,
# lon_max, lat_max).
ROUTING_BBOX = (-7.45, 40.35, -6.85, 41.05)
