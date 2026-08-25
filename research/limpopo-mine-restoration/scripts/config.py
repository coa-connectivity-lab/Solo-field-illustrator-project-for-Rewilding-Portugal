"""
config.py
─────────
Paths and CRS for the Limpopo mine-restoration/eco-connectivity study.

Conda environment: `coa` (geopandas, osmnx, requests, matplotlib all already
present there — nothing new installed for this analysis, per project
preference in CLAUDE.md).

Companion narrative deliverable: field-trips/deskStudy/
limpopo-mine-restoration-connectivity.md. This is a standalone regional study
(South Africa), not part of the Côa Valley connectivity pipeline in
research/eco-connectivity/ — kept in its own folder for the same reason
research/camargue-comparison/ is: different region, different scale, not
feeding that pipeline's resistance/suitability models.
"""

from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent.parent  # research/limpopo-mine-restoration/
DATA_RAW = THIS_DIR / "data" / "raw"
DATA_PROCESSED = THIS_DIR / "data" / "processed"
QGIS_DIR = THIS_DIR / "qgis"
OUTPUT_MAPS = THIS_DIR / "output" / "maps"
OUTPUT_TABLES = THIS_DIR / "output" / "tables"

BOUNDARY_GPKG = DATA_PROCESSED / "limpopo_boundary.gpkg"
MINING_GPKG = DATA_PROCESSED / "limpopo_mining_sites.gpkg"
PROTECTED_GPKG = DATA_PROCESSED / "limpopo_protected_areas.gpkg"
RIVERS_GPKG = DATA_PROCESSED / "limpopo_rivers.gpkg"
CONNECTIVITY_GPKG = DATA_PROCESSED / "limpopo_connectivity.gpkg"

# CRS_DISPLAY matches OSM/Wikidata native (config.CRS_DISPLAY convention already
# used in research/eco-connectivity/config.py and research/camargue-comparison/).
# CRS_METRIC: Africa Albers Equal Area Conic (ESRI:102022) — the continental-
# Africa equal-area analogue of research/eco-connectivity's EPSG:3035 (ETRS89-LAEA
# Europe), used here for all distance/area/buffer analysis. Not a UTM zone:
# Limpopo straddles UTM 35S/36S, and a single UTM zone would distort accuracy
# on the province's eastern edge (Kruger/Mapungubwe), which matters most for
# this analysis. Verified resolvable via pyproj before use (2026-08-25).
CRS_DISPLAY = "EPSG:4326"
CRS_METRIC = "ESRI:102022"

# Limpopo province boundary, OSM relation 349547 (boundary=administrative),
# confirmed via direct Nominatim query 2026-08-25. Bounding box used for the
# initial bbox pulls below is deliberately generous and gets clipped to this
# polygon afterward — a naive bbox alone also catches real North West Province
# platinum-belt mines (Bafokeng, Crocodile River, Eland, near Rustenburg) and
# Mpumalanga's Sabi Sands Game Reserve, confirmed during planning research.
LIMPOPO_OSM_RELATION = "R349547"

# Generous discovery bbox (lon_min, lat_min, lon_max, lat_max) — over-inclusive
# on purpose; every record pulled with it is clipped to the real province
# polygon before being treated as a Limpopo record.
DISCOVERY_BBOX = (26.3, -25.6, 31.9, -22.0)

USER_AGENT = "linda-limpopo-mine-restoration-research/1.0"
