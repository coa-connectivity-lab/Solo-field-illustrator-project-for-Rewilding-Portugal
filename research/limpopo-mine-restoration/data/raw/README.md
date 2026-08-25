# data/raw

Empty by design. This study's automated pipeline (`scripts/acquire_*.py`) pulls
from Wikidata and OpenStreetMap directly, no raw files are staged here.

## Manual upgrade path: South Africa's official SAPAD protected-areas database

`egis.environment.gov.za`, which hosts DFFE's South African Protected and
Conservation Areas Database (SAPAD/PACA, updated quarterly, non-commercial
use permitted per the portal's own terms), returned a connection failure
from the working environment this study was built in. If you can reach that
host directly:

1. Download the current SAPAD shapefile release from
   https://egis.environment.gov.za/protected_and_conservation_areas_database
   (or via SANBI's BGIS portal, https://bgis.sanbi.org, Spatial Datasets
   section).
2. Place the extracted shapefile(s) in this folder.
3. `scripts/acquire_protected_areas.py` currently builds `protected_areas`
   entirely from Wikidata + OSM (see that script's own docstring). Extending
   it to read a local SAPAD shapefile from this folder, clip it to the
   Limpopo boundary, and either replace or cross-check the existing
   OSM-polygon records is the natural next step, not yet implemented.

No equivalent path exists for the mining side: DMRE's SAMRAD cadastre had
its public GIS viewer disabled by the department itself, with no public
replacement live as of the sources checked in this study's report
(`field-trips/deskStudy/limpopo-mine-restoration-connectivity.md`, section 4).
