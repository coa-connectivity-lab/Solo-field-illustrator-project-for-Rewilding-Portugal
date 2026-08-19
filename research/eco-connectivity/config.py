"""
config.py
─────────
Single source of truth for paths, CRS, study area, and the three
land/water/air functional groups used throughout the Côa Valley
eco-connectivity notebook.

Conda environment: `coa` (see /home/linda/Documents/myData/data-management/environment-coa.yml).
Geospatial stack: pandas, geopandas, rioxarray/xarray, scikit-learn, per project preference
(CLAUDE.md) — no new packages have been installed for this analysis; everything below runs
on what's already in that environment.
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

STUDY_AREA_BUFFER_KM = 30.0  # radius around the Côa centerline
RASTER_RESOLUTION_M = 100.0  # matches data-management base layers

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

# ── Land tenure context (asset-or-barrier, not folded into resistance) ──────

FAIA_BRAVA_NOTE = (
    "Private nature reserve in the Greater Côa Valley, associated with "
    "Rewilding Portugal / Rewilding Europe. Boundary not yet in this repo — "
    "acquire in acquire_reserves_and_hunting_zones.py."
)
