"""
acquire_field_observations.py
───────────────────────────────
Load the Survey123 "coa-connectivity-lab-survey" field export (12 visit
records, prototype/test data per survey123/memo-data-use.md — not yet real
fieldwork, but real GPS locations used here as the "visited sites" layer).

Safe-and-just handling: any record whose free-text fields mention a
sensitive species (config.SENSITIVE_SPECIES) has its coordinates
generalised to a coarse grid before being written out, per the open
data-handling item in survey123/memo-data-use.md. This project has no
wildcat records yet, but the check runs on every future export too.
"""

import zipfile

import geopandas as gpd
import pandas as pd

import config

GDB_ZIP = config.SURVEY123_FGDB_ZIP
LAYER = "survey"
OUT_GPKG = config.DATA_PROCESSED / "field_observations.gpkg"
EXTRACT_DIR = config.DATA_RAW / "survey123_fgdb"


def _extracted_gdb_path() -> str:
    if not EXTRACT_DIR.exists():
        EXTRACT_DIR.mkdir(parents=True)
        with zipfile.ZipFile(GDB_ZIP) as zf:
            zf.extractall(EXTRACT_DIR)
    gdb = next(p for p in EXTRACT_DIR.iterdir() if p.suffix == ".gdb")
    return str(gdb)

SENSITIVE_KEYWORDS = ["felis silvestris", "wildcat", "gato-bravo", "gato bravo"]


def _is_sensitive(row: pd.Series) -> bool:
    text = " ".join(str(v) for v in row.values if isinstance(v, str)).lower()
    return any(kw in text for kw in SENSITIVE_KEYWORDS)


def _snap_to_grid(geom, cell_km: float):
    cell_m = cell_km * 1000
    x = (geom.x // cell_m) * cell_m + cell_m / 2
    y = (geom.y // cell_m) * cell_m + cell_m / 2
    return geom.__class__(x, y)


def main() -> None:
    gdf = gpd.read_file(_extracted_gdb_path(), layer=LAYER)
    if gdf.crs is None:
        gdf = gdf.set_crs(config.CRS_DISPLAY)
    gdf = gdf.to_crs(config.CRS_METRIC)

    gdf["sensitive"] = gdf.apply(_is_sensitive, axis=1)
    n_sensitive = int(gdf["sensitive"].sum())
    if n_sensitive:
        mask = gdf["sensitive"]
        gdf.loc[mask, "geometry"] = gdf.loc[mask, "geometry"].apply(
            lambda g: _snap_to_grid(g, config.SENSITIVE_LOCATION_BUFFER_KM)
        )
    gdf["location_precision"] = gdf["sensitive"].map(
        {True: "generalized", False: "exact"}
    )

    keep_cols = ["site_name", "date_and_time", "sensitive", "location_precision", "geometry"]
    gdf[keep_cols].to_file(OUT_GPKG, layer="visited_sites", driver="GPKG")

    print(f"{len(gdf)} field visits loaded, {n_sensitive} flagged sensitive and generalised")
    print(f"Wrote {OUT_GPKG}")


if __name__ == "__main__":
    main()
