"""
acquire_gbif_occurrences.py
────────────────────────────
Read the cached GBIF Darwin Core Archive downloads for the 9 focal species
(all already present at data-management/data/raw/gbif/<Species>.zip — no
fresh API pull needed, see docs/01_data_sources.md for the DOIs) and clip
to the Côa Valley study area.

Coordinate-uncertainty note: several species here (wolf, wildcat) have GBIF
records with coordinates deliberately generalised to protect the species
(one wolf record in this dataset is offset by ~28km). A strict <1km filter
(as used in Prima et al. 2024, p.2388, at national scale with 193 species)
would leave almost nothing for a 30km-radius regional study of sensitive
carnivores, so this project uses a permissive threshold instead and states
it plainly as a limitation in the notebook rather than silently keeping
Prima's number.
"""

import io
import zipfile

import geopandas as gpd
import pandas as pd

import config

COORD_UNCERTAINTY_MAX_M = 30_000  # permissive - see module docstring
COLUMNS = [
    "gbifID", "species", "decimalLatitude", "decimalLongitude",
    "coordinateUncertaintyInMeters", "eventDate", "year",
    "basisOfRecord", "countryCode",
]

OUT_GPKG = config.DATA_PROCESSED / "gbif_occurrences.gpkg"


def read_species_occurrences(zip_stem: str) -> pd.DataFrame:
    zip_path = config.DATA_MGMT_GBIF / f"{zip_stem}.zip"
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open("occurrence.txt") as f:
            df = pd.read_csv(
                io.TextIOWrapper(f, encoding="utf-8"),
                sep="\t",
                usecols=lambda c: c in COLUMNS,
                low_memory=False,
            )
    return df


def to_points(df: pd.DataFrame, group_key: str, zip_stem: str) -> gpd.GeoDataFrame:
    df = df.dropna(subset=["decimalLatitude", "decimalLongitude"]).copy()
    df = df[df["coordinateUncertaintyInMeters"].isna() | (df["coordinateUncertaintyInMeters"] <= COORD_UNCERTAINTY_MAX_M)]
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["decimalLongitude"], df["decimalLatitude"]),
        crs=config.CRS_DISPLAY,
    )
    gdf["group"] = group_key
    gdf["gbif_zip_stem"] = zip_stem
    return gdf


def main() -> None:
    study_area = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="study_area")
    study_area_metric = study_area.to_crs(config.CRS_METRIC)

    first_layer = True
    for group in config.GROUPS.values():
        parts = []
        for sp in group.species:
            df = read_species_occurrences(sp.gbif_zip_stem)
            gdf = to_points(df, group.key, sp.gbif_zip_stem)
            parts.append(gdf)
            print(f"  {sp.scientific_name} ({sp.gbif_zip_stem}): {len(df)} raw -> {len(gdf)} usable")

        group_gdf = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=config.CRS_DISPLAY)
        group_gdf_metric = group_gdf.to_crs(config.CRS_METRIC)
        clipped = gpd.clip(group_gdf_metric, study_area_metric)

        mode = "w" if first_layer else "a"
        clipped.to_file(OUT_GPKG, layer=f"{group.key}_occurrences", driver="GPKG", mode=mode)
        first_layer = False
        print(f"{group.label}: {len(group_gdf)} total, {len(clipped)} within {config.STUDY_AREA_BUFFER_KM}km study area")

    print(f"Wrote {OUT_GPKG}")


if __name__ == "__main__":
    main()
