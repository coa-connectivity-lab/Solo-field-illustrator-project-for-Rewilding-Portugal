"""
config.py
─────────
Single source of truth for paths, CRS, study area, and the three
land/water/air functional groups used throughout the Côa Valley
eco-connectivity notebook.

Conda environment: `coa` (see /home/linda/Documents/myData/data-management/environment-coa.yml).
Geospatial stack: pandas, geopandas, rioxarray/xarray, scikit-learn, per project preference
(CLAUDE.md) — no new packages have been installed for this analysis; everything below runs
on what's already in that environment, including the v2 additions (catchment tracing,
fire history via `pystac_client`/`planetary_computer`, both already present in `coa`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ── Repos ────────────────────────────────────────────────────────────────────

THIS_REPO = Path(__file__).resolve().parents[2]
ECO_DIR = Path(__file__).resolve().parent

# Sibling repo this project draws raw data from (GBIF downloads, EEA/Copernicus
# layers, DEM-derived base layers). Read-only: never write into this path.
DATA_MGMT_REPO = Path("/home/linda/Documents/myData/data-management")
DATA_MGMT_RAW = DATA_MGMT_REPO / "data" / "raw"
DATA_MGMT_BASE_LAYERS = DATA_MGMT_REPO / "data" / "processed" / "base_layers"
DATA_MGMT_GBIF = DATA_MGMT_RAW / "gbif"

# This project's own folders
DATA_RAW = ECO_DIR / "data" / "raw"
DATA_PROCESSED = ECO_DIR / "data" / "processed"
OUTPUT_RASTERS = ECO_DIR / "output" / "rasters"
OUTPUT_MAPS = ECO_DIR / "output" / "maps"
OUTPUT_TABLES = ECO_DIR / "output" / "tables"

# Sibling references folder (this repo, read-only): Rewilding Portugal's 2025
# annual review PDF + the flagship-species/aggregate-counts CSVs extracted from
# it in a prior session, and the endangeredlandscapes.org project page.
REFERENCES_DIR = THIS_REPO / "references" / "ecological-information"
ANNUAL_REVIEW_SPECIES_CSV = REFERENCES_DIR / "data" / "annual_review_2025_species.csv"
ANNUAL_REVIEW_COUNTS_CSV = REFERENCES_DIR / "data" / "annual_review_2025_aggregate_counts.csv"

# National river-network dataset used to trace the Côa's own tributary
# catchment (HydroRIVERS, part of the HydroSHEDS family; global file, always
# read with a bbox filter — never load unfiltered).
HYDRORIVERS_GPKG = DATA_MGMT_RAW / "colab" / "hydrorivers_100.gpkg"
HYDRORIVERS_LAYER = "rivers"
# Generous regional bbox for the initial HydroRIVERS read (lon_min, lat_min, lon_max,
# lat_max, EPSG:4326) — wide enough to comfortably contain the Côa's own catchment
# plus the Douro confluence point, without loading the full 2.6M-feature global file.
HYDRORIVERS_REGIONAL_BBOX = (-8.3, 39.6, -6.0, 41.6)

for _d in (DATA_RAW, DATA_PROCESSED, OUTPUT_RASTERS, OUTPUT_MAPS, OUTPUT_TABLES):
    _d.mkdir(parents=True, exist_ok=True)

# Field data (this project's own Survey123 export + field-trip notes)
SURVEY123_FGDB_ZIP = THIS_REPO / "geoData" / "FGDB.zip"
COA_RIVER_GPKG = (
    THIS_REPO
    / "research"
    / "geoAI_tests"
    / "assignment_submission"
    / "assignment"
    / "data"
    / "processed"
    / "coa_river.gpkg"
)

# ── CRS ──────────────────────────────────────────────────────────────────────

CRS_DISPLAY = "EPSG:4326"    # field data, GBIF, web maps
CRS_METRIC = "EPSG:3035"     # ETRS89-LAEA Europe — matches data-management base layers, 100m grid

# ── Study area ───────────────────────────────────────────────────────────────

STUDY_AREA_BUFFER_KM = 30.0     # radius around the Côa centerline (mainstem)
TRIBUTARY_BUFFER_KM = 30.0      # same radius applied around the traced tributary network
RASTER_RESOLUTION_M = 100.0     # matches data-management base layers

# Snap tolerance for matching the OSM-derived Côa centerline onto HydroRIVERS reaches.
CATCHMENT_SNAP_BUFFER_M = 300.0
# The Côa's real drainage-basin area is ~2,495 km2 (published figure). The 300m snap
# buffer around the OSM line also touches the Douro mainstem right at the confluence,
# whose own upstream area is ~80,000+ km2 — this ceiling excludes those accidentally-
# matched Douro reaches when picking the Côa's own mouth reach (max UPLAND_SKM below
# this ceiling), rather than fabricating a hardcoded HYRIV_ID.
CATCHMENT_MAX_PLAUSIBLE_UPLAND_SKM = 10_000.0

# Rewilding Portugal's own Greater Côa Valley project footprint, per the annual review
# and the Endangered Landscapes & Seascapes Programme project page (references/
# ecological-information/endangeredlandscapes-org-project-greater-coa-valley.pdf) — no
# boundary polygon exists for this anywhere in either repo, only this prose figure.
# Documented for comparison against the river-buffer study area, not used to build a
# fabricated boundary geometry.
REWILDING_PORTUGAL_PROJECT_AREA_HA = 318_000.0

# ── Functional groups: land / water / air ───────────────────────────────────


@dataclass(frozen=True)
class Species:
    gbif_zip_stem: str        # matches data-management/data/raw/gbif/<stem>.zip
    scientific_name: str
    common_name: str
    dispersal_km: float       # sets the circuit-theory search radius


@dataclass(frozen=True)
class Group:
    key: str
    label: str
    narrative_plate: str      # which field-trip chapter this reads onto
    species: list[Species] = field(default_factory=list)
    resistance_shape_c: float = 4.0  # Prima et al. 2024 Eq.1, mid-range default

    @property
    def dispersal_km(self) -> float:
        """Radius parameter: the group's largest member sets the search window."""
        return max(sp.dispersal_km for sp in self.species)


GROUPS: dict[str, Group] = {
    "land": Group(
        key="land",
        label="Land",
        narrative_plate="Movement (Vale Carapito) / Connection (Ribeira do Mosteiro)",
        species=[
            Species("Canis_lupus", "Canis lupus", "Iberian wolf", dispersal_km=80.0),
            Species("Felis_silvestris", "Felis silvestris", "European wildcat", dispersal_km=15.0),
            Species("Cervus_elaphus", "Cervus elaphus", "Red deer", dispersal_km=30.0),
        ],
    ),
    "water": Group(
        key="water",
        label="Water",
        narrative_plate="Water (Paul de Toirões)",
        species=[
            Species("Lutra_lutra", "Lutra lutra", "Eurasian otter", dispersal_km=20.0),
            Species("P_polylepis", "Pseudochondrostoma polylepis", "Iberian nase", dispersal_km=10.0),
            Species("Squalius_alburnoides", "Squalius alburnoides", "Calandino", dispersal_km=10.0),
            Species("Emys_orbicularis", "Emys orbicularis", "European pond turtle", dispersal_km=5.0),
        ],
    ),
    "air": Group(
        key="air",
        label="Air",
        narrative_plate="Douro Superior / Côa gorge raptor corridor",
        species=[
            Species("Gyps_fulvus", "Gyps fulvus", "Griffon vulture", dispersal_km=100.0),
            Species("N_percnopterus", "Neophron percnopterus", "Egyptian vulture", dispersal_km=100.0),
            Species("Aquila_chrysaetos", "Aquila chrysaetos", "Golden eagle", dispersal_km=60.0),
        ],
    ),
}

# Sensitive species: locations must be generalized/buffered before any figure,
# map, or export leaves this repo — see survey123/memo-data-use.md open item.
SENSITIVE_SPECIES = {"Felis_silvestris"}
SENSITIVE_LOCATION_BUFFER_KM = 5.0

# ── Fire history (barrier to land restoration) ──────────────────────────────

# EFFIS's own historical burnt-area archive needs a manual data-request form, and its
# live WFS layer errored server-side (Oracle Spatial connection failure) when tried in
# this session — neither is usable for automated acquisition. Real alternative: NASA's
# MODIS Burned Area Monthly product (MCD64A1.061), served as public, no-auth
# Cloud-Optimized GeoTIFFs via Microsoft Planetary Computer's STAC API (confirmed
# reachable this session). 500m resolution, monthly, 2000-present.
FIRE_STAC_API_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
FIRE_STAC_COLLECTION = "modis-64A1-061"
FIRE_HISTORY_START = "2015-01-01"   # 10 recent fire seasons — matches the "recent fire
FIRE_HISTORY_END = "2025-12-31"     # history" framing of the annual review's 2025 fires
# Land-resistance fire penalty (build_resistance_surfaces.py): burned cells are pushed
# toward the resistance ceiling, scaled by how recently they burned within the window
# above. Applied to the land group only, per the "fire as a barrier to land
# restoration" ask — water/air groups are left untouched (see notebook Open Items for
# the un-modeled post-fire erosion/sediment question on the water side).
FIRE_RESISTANCE_MAX_PENALTY = 60.0   # added to base resistance for a cell burned in FIRE_HISTORY_END's year
FIRE_RESISTANCE_MIN_PENALTY = 10.0   # added for a cell last burned at the start of the window
FIRE_RESISTANCE_CEILING = 100.0      # same ceiling as the existing Prima et al. Eq.1 resistance range

# ── Land tenure context (asset-or-barrier, not folded into resistance) ──────

FAIA_BRAVA_NOTE = (
    "Private nature reserve in the Greater Côa Valley, associated with "
    "Rewilding Portugal / Rewilding Europe. Boundary not yet in this repo — "
    "acquire in acquire_reserves_and_hunting_zones.py."
)
