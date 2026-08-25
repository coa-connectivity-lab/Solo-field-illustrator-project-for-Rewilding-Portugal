"""
acquire_field_observations.py
───────────────────────────────
Load the Survey123 "coa-connectivity-lab-survey" field export. v3: swapped
from the FGDB export (geoData/FGDB.zip, 12 rows, config.SURVEY123_FGDB_ZIP)
to the CSV export (geoData/CSV.zip -> survey_0.csv, 22 rows,
config.SURVEY123_CSV_ZIP) — a later/richer pull of the SAME Survey123 form.
Verified before this switch: the CSV's first 12 rows are byte-identical
(site_name, date_and_time, x/y) to the FGDB's 12 `visited_sites` records
already in field_observations.gpkg. The CSV adds 10 new site visits, plus
up to 3 repeated species-observation blocks and up to 3 repeated
barrier-observation blocks per row (Survey123's repeat-group export
convention — pandas auto-suffixes the duplicate CSV headers .1/.2 on read).

v4: the same CSV export has grown from 22 to 26 rows. The 4 new rows (indices
22-25) are NOT real field visits — they're desk-study reference pins Linda
added to the same Survey123 form while researching comparison regions:
"Avignon and the Camargue" (France), "Mine Restoration and Ecological
Connectivity in Limpopo Province" (South Africa), "Forêt de Fontainebleau"
(France), and "Ermo das Águias — Mixed Mediterranean Habitat Mosaic" (Côa
Valley itself). The first three sit real-world outside the Côa study area
entirely; only the Ermo das Águias pin falls inside it. All four have a
blank `Date and time` field, which the v3 strict-format date parser would
crash on — see the `errors="coerce"` fix below. See `in_study_area` on
`visited_sites` for how downstream consumers filter these out without
guessing.

Three output layers in field_observations.gpkg:
  visited_sites        - one row per survey visit (unchanged shape/logic,
                          now CSV-sourced): site_name, date_and_time,
                          sensitive, location_precision, in_study_area,
                          geometry.
  species_observations  - long-form melt of the 3 species blocks, one row per
                          non-null "Functional group" slot. Narrative-only:
                          species identity here is often uncertain in the
                          field notes themselves (e.g. "possible Sorraia
                          phenotype", "unconfirmed — flag as unclear") — this
                          is NOT fed into build_suitability_models.py and is
                          NOT reconciled against config.GROUPS' land/water/air
                          species keys.
  barrier_observations  - long-form melt of the 3 barrier blocks, one row per
                          non-null "Barrier type" slot (deliberately NOT keyed
                          on the permeability or notes fields — inspection of
                          the raw CSV found 4 rows (site rows 3,4,5,6 in the
                          0-indexed CSV) whose second barrier slot carries only
                          a boilerplate "TODO: there's already baseline
                          biodiversity signage..." note with no Barrier type
                          selected in that slot; keying the melt on the notes
                          field instead of Barrier type would manufacture 4
                          phantom barrier rows with no real barrier type. The
                          "Other - Permeability assessment"/".1" trailing
                          columns were also checked directly against the raw
                          csv text and are empty for every row in this export).
                          Adds a boolean `resistance_eligible` column - see
                          _classify_other_barrier() below for the "other"-type
                          resolution logic (fire/vegetation-disturbance notes
                          and free-text-less "other" rows are excluded; the
                          one legitimate "other" row, Ponte da União, has real
                          free text ("Bridge") and is resolved to that type).

Safe-and-just handling (unchanged): any source CSV row whose free-text fields
(now scanning all 48 CSV columns, including the new species/barrier text)
mention a sensitive species (config.SENSITIVE_SPECIES) has its coordinates
generalised to a coarse grid before being written out, per the open
data-handling item in survey123/memo-data-use.md. This export still has zero
wildcat records (checked), but the check runs on every future export too.
The species_observations and barrier_observations layers inherit the same
(possibly generalised) geometry as their parent visited_sites row, so the
safety behaviour is consistent across all three layers.
"""

import zipfile
from io import BytesIO

import geopandas as gpd
import pandas as pd

import config

CSV_ZIP = config.SURVEY123_CSV_ZIP
CSV_NAME = "survey_0.csv"
OUT_GPKG = config.DATA_PROCESSED / "field_observations.gpkg"

SENSITIVE_KEYWORDS = ["felis silvestris", "wildcat", "gato-bravo", "gato bravo"]

SPECIES_BLOCK_BASE_COLS = [
    "Functional group",
    "Species name or common name",
    "Count or abundance estimate",
    "Behaviour notes",
    "Habitat or microhabitat description",
    "Does this observation relate to restoration evidence?",
]
SPECIES_OUT_COLS = [
    "functional_group", "species_name", "count_or_abundance",
    "behaviour_notes", "habitat_description", "restoration_evidence",
]

BARRIER_BLOCK_BASE_COLS = [
    "Barrier type",
    "Other - Barrier type",
    "Permeability assessment",
    "How does this barrier affect movement between habitats?",
]

BLOCK_SUFFIXES = ["", ".1", ".2"]

# Free-text phrases that self-identify a Survey123 "other"-typed barrier row as
# describing a temporary fire/vegetation-disturbance event rather than a real
# physical barrier (see Amoreira/Castelo Mendo and Ermo das Águias rows).
FIRE_DISTURBANCE_KEYWORDS = [
    "not a physical barrier",
    "rather than a physical barrier",
    "not infrastructure",
]


def _read_csv() -> pd.DataFrame:
    with zipfile.ZipFile(CSV_ZIP) as zf:
        with zf.open(CSV_NAME) as f:
            return pd.read_csv(BytesIO(f.read()), encoding="utf-8-sig")


def _is_sensitive(row: pd.Series) -> bool:
    text = " ".join(str(v) for v in row.values if isinstance(v, str)).lower()
    return any(kw in text for kw in SENSITIVE_KEYWORDS)


def _snap_to_grid(geom, cell_km: float):
    cell_m = cell_km * 1000
    x = (geom.x // cell_m) * cell_m + cell_m / 2
    y = (geom.y // cell_m) * cell_m + cell_m / 2
    return geom.__class__(x, y)


def _is_fire_disturbance_note(text) -> bool:
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(kw in t for kw in FIRE_DISTURBANCE_KEYWORDS)


def _classify_other_barrier(other_text, notes_text) -> tuple[str, bool, str | None]:
    """Resolve a Barrier type == 'other' row. Returns (resolved_type, resistance_eligible, reason)."""
    if _is_fire_disturbance_note(other_text) or _is_fire_disturbance_note(notes_text):
        return "other", False, "fire/vegetation-disturbance note, not a physical barrier"
    if isinstance(other_text, str) and other_text.strip():
        return other_text.strip(), True, None
    return "other", False, "no 'Other - Barrier type' free text - barrier type genuinely unknown"


def _melt_species(base: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    records = []
    for _, row in base.iterrows():
        for suffix in BLOCK_SUFFIXES:
            fg = row.get(f"Functional group{suffix}")
            if pd.isna(fg):
                continue
            rec = {"site_name": row["site_name"], "date_and_time": row["date_and_time"]}
            for base_col, out_col in zip(SPECIES_BLOCK_BASE_COLS, SPECIES_OUT_COLS):
                rec[out_col] = row.get(f"{base_col}{suffix}")
            rec["geometry"] = row["geometry"]
            records.append(rec)
    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs=base.crs)
    return gdf


def _melt_barriers(base: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    records = []
    for _, row in base.iterrows():
        for suffix in BLOCK_SUFFIXES:
            barrier_type = row.get(f"Barrier type{suffix}")
            if pd.isna(barrier_type):
                continue
            other_text = row.get(f"Other - Barrier type{suffix}")
            permeability = row.get(f"Permeability assessment{suffix}")
            notes = row.get(
                f"How does this barrier affect movement between habitats?{suffix}"
            )

            if barrier_type == "other":
                resolved_type, eligible, reason = _classify_other_barrier(other_text, notes)
            else:
                resolved_type, eligible, reason = barrier_type, True, None

            records.append({
                "site_name": row["site_name"],
                "date_and_time": row["date_and_time"],
                "barrier_type": resolved_type,
                "permeability_assessment": permeability,
                "effect_on_movement_notes": notes,
                "x": row["_raw_x"],
                "y": row["_raw_y"],
                "resistance_eligible": eligible,
                "_exclusion_reason": reason,
                "geometry": row["geometry"],
            })
    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs=base.crs)
    return gdf


def main() -> None:
    df = _read_csv()
    print(f"Read {len(df)} rows from {CSV_ZIP.name}::{CSV_NAME}")

    df["sensitive"] = df.apply(_is_sensitive, axis=1)
    n_sensitive = int(df["sensitive"].sum())

    geometry = gpd.points_from_xy(df["x"], df["y"])
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=config.CRS_DISPLAY).to_crs(config.CRS_METRIC)
    gdf["_raw_x"] = df["x"].values
    gdf["_raw_y"] = df["y"].values
    gdf = gdf.rename(columns={"Site name": "site_name", "Date and time": "date_and_time"})
    gdf["date_and_time"] = pd.to_datetime(
        gdf["date_and_time"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce"
    ).dt.tz_localize("UTC")
    n_no_date = int(gdf["date_and_time"].isna().sum())
    if n_no_date:
        print(f"  {n_no_date} row(s) have no Date and time (desk-study reference pins, not real visits): "
              f"{sorted(gdf.loc[gdf['date_and_time'].isna(), 'site_name'].tolist())}")

    if n_sensitive:
        mask = gdf["sensitive"]
        gdf.loc[mask, "geometry"] = gdf.loc[mask, "geometry"].apply(
            lambda g: _snap_to_grid(g, config.SENSITIVE_LOCATION_BUFFER_KM)
        )
    gdf["location_precision"] = gdf["sensitive"].map({True: "generalized", False: "exact"})

    study_area = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="study_area")
    minx, miny, maxx, maxy = study_area.to_crs(config.CRS_METRIC).total_bounds
    gdf["in_study_area"] = gdf.geometry.x.between(minx, maxx) & gdf.geometry.y.between(miny, maxy)

    # ── visited_sites (v4 adds in_study_area) ───────────────────────────────
    keep_cols = ["site_name", "date_and_time", "sensitive", "location_precision", "in_study_area", "geometry"]
    gdf[keep_cols].to_file(OUT_GPKG, layer="visited_sites", driver="GPKG")
    is_reference_pin = gdf["date_and_time"].isna()
    n_real_visits = int((~is_reference_pin).sum())
    n_pins_out_of_area = int((is_reference_pin & ~gdf["in_study_area"]).sum())
    n_visits_out_of_area = int((~is_reference_pin & ~gdf["in_study_area"]).sum())
    print(f"visited_sites: {len(gdf)} total rows -> {n_real_visits} real field visits "
          f"({n_visits_out_of_area} of those outside the study area, e.g. the Douro estuary/coast day trip), "
          f"{n_no_date} desk-study reference pins ({n_pins_out_of_area} of those outside the study area), "
          f"{n_sensitive} flagged sensitive and generalised")

    # ── species_observations (narrative only) ───────────────────────────────
    species = _melt_species(gdf)
    # mode="w" (not "a"): this must OVERWRITE the layer on each run, not append rows to
    # it - GPKG write-mode is per-layer in this environment (confirmed: repeated runs
    # with visited_sites' plain to_file(), which defaults to mode="w", stay at a stable
    # row count rather than wiping sibling layers), so "w" here is layer-safe. "a" was
    # found to silently accumulate duplicate rows across repeated script runs (25 -> 50
    # -> 75...), which is not the intended behaviour - the printed row counts below are
    # meant to describe this run's fresh export, not a running total.
    species.to_file(OUT_GPKG, layer="species_observations", driver="GPKG", mode="w")
    print(f"species_observations: {len(species)} rows "
          f"(non-null Functional group slots across {len(gdf)} source rows)")

    # ── barrier_observations ────────────────────────────────────────────────
    barriers = _melt_barriers(gdf)
    n_eligible = int(barriers["resistance_eligible"].sum())
    n_excluded = len(barriers) - n_eligible
    print(f"barrier_observations: {len(barriers)} rows (non-null Barrier type slots)")
    print(f"  resistance_eligible: {n_eligible}, excluded: {n_excluded}")
    if n_excluded:
        for reason, count in barriers.loc[~barriers["resistance_eligible"], "_exclusion_reason"].value_counts().items():
            print(f"    - {reason}: {count}")

    out_of_bounds = ~barriers.geometry.x.between(minx, maxx) | ~barriers.geometry.y.between(miny, maxy)
    n_oob = int(out_of_bounds.sum())
    print(f"  barrier rows outside study_area.gpkg bounding box (won't rasterize onto the resistance grid): {n_oob}")
    if n_oob:
        print(f"    sites: {sorted(barriers.loc[out_of_bounds, 'site_name'].unique().tolist())}")

    # mode="w" for the same reason as species_observations above - must overwrite, not
    # accumulate rows across repeated runs.
    barriers.drop(columns=["_exclusion_reason"]).to_file(OUT_GPKG, layer="barrier_observations", driver="GPKG", mode="w")

    print(f"Wrote {OUT_GPKG} (layers: visited_sites, species_observations, barrier_observations)")


if __name__ == "__main__":
    main()
