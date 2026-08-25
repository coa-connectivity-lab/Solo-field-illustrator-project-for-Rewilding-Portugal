"""
config.py
─────────
Paths and CRS for the Fontainebleau eco-connectivity/ecotourism comparison
study (companion to field-trips/deskStudy/
fontainebleau-ecotourism-implications-coa-valley.md).

Conda environment: `coa`. Standalone regional study (France), not part of
the Côa Valley pipeline in research/eco-connectivity/, same reasoning as
research/camargue-comparison/ and research/limpopo-mine-restoration/.
"""

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent.parent  # research/fontainebleau-comparison/
DATA_RAW = THIS_DIR / "data" / "raw"
DATA_PROCESSED = THIS_DIR / "data" / "processed"
QGIS_DIR = THIS_DIR / "qgis"
OUTPUT_MAPS = THIS_DIR / "output" / "maps"
OUTPUT_TABLES = THIS_DIR / "output" / "tables"

BOUNDARY_GPKG = DATA_PROCESSED / "fontainebleau_boundary.gpkg"
PROTECTED_GPKG = DATA_PROCESSED / "fontainebleau_protected_areas.gpkg"
SPECIES_GPKG = DATA_PROCESSED / "fontainebleau_species_occurrences.gpkg"
FACILITIES_GPKG = DATA_PROCESSED / "fontainebleau_ecotourism_facilities.gpkg"

# CRS_DISPLAY matches OSM/Wikidata/GBIF native format.
# CRS_METRIC: RGF93 / Lambert-93 (EPSG:2154) - France's own standard official
# projected CRS (used by IGN, INPN, all French government GIS), the correct,
# deliberate choice for a French national-scale study, distinct from the
# Europe-wide EPSG:3035 used for research/camargue-comparison/research/eco-
# connectivity. Verified resolvable via pyproj before use (2026-08-25).
CRS_DISPLAY = "EPSG:4326"
CRS_METRIC = "EPSG:2154"

USER_AGENT = "linda-fontainebleau-research/1.0"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Discovery bbox (lon_min, lat_min, lon_max, lat_max) around the Fontainebleau
# massif, deliberately generous - confirmed via Overpass during planning to
# actually contain the real forest (bounds ~2.56-2.81 lon, 48.32-48.51 lat),
# with margin.
DISCOVERY_BBOX = (2.45, 48.30, 2.85, 48.50)
