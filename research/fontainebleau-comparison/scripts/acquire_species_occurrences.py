"""
acquire_species_occurrences.py
──────────────────────────────────
Species occurrence records for the Fontainebleau massif, live from GBIF's
public occurrence-search API (api.gbif.org, confirmed reachable during
planning, no API key required for this endpoint). This is a different
approach from the Côa Valley pipeline's own acquire_gbif_occurrences.py,
which reads pre-downloaded Darwin Core Archive zips staged locally for 9
Côa-specific focal species - not reusable here, since this is a different
country and a different, broader taxonomic question ("what's actually
recorded here" rather than "confirm these 9 named species").

Query design: one bbox-filtered search per taxonomic class (Mammalia, Aves,
Reptilia, Amphibia, Insecta, Tracheophyta/vascular plants), each capped at a
few hundred records and sorted by most-recent, rather than one unfiltered
pull - GBIF's Fontainebleau-area record count is large (a heavily-recorded,
well-studied forest near Paris) and an uncapped pull isn't necessary for a
regional screening study. This is Sourced data throughout: every record
carries GBIF's own gbifID, so any individual occurrence can be traced back.

Writes: data/processed/fontainebleau_species_occurrences.gpkg, layer "occurrences"
"""

import geopandas as gpd
import pandas as pd
import requests

import config

GBIF_URL = "https://api.gbif.org/v1/occurrence/search"
PER_CLASS_LIMIT = 300  # GBIF API page-size cap per request; enough for a screening-level map

# GBIF's occurrence-search API silently ignores free-text "class"/"kingdom"
# filter values (confirmed during acquisition: class=Aves and class=Mammalia
# returned byte-identical result sets and identical counts - not a filter at
# all). The working filter is taxonKey, GBIF's own backbone-taxonomy numeric
# ID, verified individually via /v1/species/match before use here. Reptilia
# has no single clean backbone class key in GBIF's checklist (a real
# consequence of reptiles being paraphyletic without birds in modern
# taxonomy, not a lookup mistake) - Squamata (lizards and snakes, backbone
# key 11592253) used instead, which covers Fontainebleau's best-known
# reptile specialist, the sand lizard Lacerta agilis.
TAXONOMIC_GROUPS = [
    (359, "Mammalia", "mammal"),
    (212, "Aves", "bird"),
    (11592253, "Squamata", "reptile (Squamata only - see module docstring)"),
    (131, "Amphibia", "amphibian"),
    (216, "Insecta", "insect"),
    (7707728, "Tracheophyta", "vascular plant"),
]

MIN_LON, MIN_LAT, MAX_LON, MAX_LAT = 2.45, 48.30, 2.85, 48.50


def fetch_class(taxon_key: int, class_name: str, group_label: str) -> pd.DataFrame:
    params = {
        "taxonKey": taxon_key,
        "decimalLongitude": f"{MIN_LON},{MAX_LON}",
        "decimalLatitude": f"{MIN_LAT},{MAX_LAT}",
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "limit": PER_CLASS_LIMIT,
    }
    resp = requests.get(GBIF_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    records = data.get("results", [])
    rows = []
    for r in records:
        if r.get("decimalLatitude") is None or r.get("decimalLongitude") is None:
            continue
        rows.append({
            "gbifID": r.get("gbifID") or r.get("key"),
            "scientific_name": r.get("scientificName"),
            "species": r.get("species"),
            "taxon_class": class_name,
            "group": group_label,
            "event_date": r.get("eventDate"),
            "year": r.get("year"),
            "basis_of_record": r.get("basisOfRecord"),
            "recorded_by": r.get("recordedBy"),
            "coordinate_uncertainty_m": r.get("coordinateUncertaintyInMeters"),
            "lon": r["decimalLongitude"],
            "lat": r["decimalLatitude"],
        })
    print(f"  {class_name} ({group_label}): {data.get('count', 0)} total records on GBIF in this bbox, "
          f"{len(rows)} fetched (page limit {PER_CLASS_LIMIT})")
    return pd.DataFrame(rows)


def main() -> None:
    boundary = gpd.read_file(config.BOUNDARY_GPKG, layer="fontainebleau_boundary")

    frames = []
    for taxon_key, class_name, group_label in TAXONOMIC_GROUPS:
        df = fetch_class(taxon_key, class_name, group_label)
        if not df.empty:
            frames.append(df)

    all_df = pd.concat(frames, ignore_index=True)
    gdf = gpd.GeoDataFrame(
        all_df, geometry=gpd.points_from_xy(all_df["lon"], all_df["lat"]), crs=config.CRS_DISPLAY
    )

    pre_clip = len(gdf)
    clipped = gpd.clip(gdf, boundary)
    print(f"\n{pre_clip} total occurrences in the discovery bbox -> {len(clipped)} within the forest boundary")

    clipped["source"] = "GBIF Occurrence API (api.gbif.org), live bbox search"
    clipped["retrieved"] = "2026-08-25"

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    clipped.drop(columns=["lon", "lat"]).to_file(config.SPECIES_GPKG, layer="occurrences", driver="GPKG")
    clipped.drop(columns="geometry").to_csv(config.OUTPUT_TABLES / "species_occurrences.csv", index=False)

    print("\nBy group:")
    print(clipped["group"].value_counts().to_string())
    print("\nTop species by record count:")
    print(clipped["species"].value_counts().head(20).to_string())
    print(f"\nWrote {config.SPECIES_GPKG}")


if __name__ == "__main__":
    main()
