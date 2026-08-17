"""
Exploratory data analysis of the City of London Police street-level crime data
for 2024 (data/london_crime_2024/YYYY-MM/*.csv, one file per month, in the
standard data.police.uk export format).

Outputs (written next to this script):
  - crime_types_bar.png          total crime count by crime type
  - crime_types_treemap.png      crime type breakdown as a treemap (Mondrian-style)
  - monthly_trend_total.png      total crime count by month
  - monthly_trend_top_types.png  monthly count for the top crime types
  - london_crime_2024_locations.geojson   point geometry for every geolocated crime

Run with:
  /home/linda/anaconda3/envs/claude_code_workshop/bin/python eda_london_crime_2024.py
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import squarify
from matplotlib.colors import LinearSegmentedColormap

DATA_DIR = Path(__file__).resolve().parent.parent / "london_crime_2024"
OUT_DIR = Path(__file__).resolve().parent

# Validated categorical palette (dataviz skill, references/palette.md), fixed order.
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7", "#e34948"]
SEQUENTIAL_BLUE = "#2a78d6"
GRID_COLOR = "#d9d9d6"
TEXT_SECONDARY = "#52514e"

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data() -> pd.DataFrame:
    files = sorted(DATA_DIR.glob("*/*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found under {DATA_DIR}")

    frames = []
    print("Files loaded:")
    for f in files:
        df = pd.read_csv(f, dtype=str)
        print(f"  {f.relative_to(DATA_DIR.parent)}: {len(df)} rows")
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined["Longitude"] = pd.to_numeric(combined["Longitude"], errors="coerce")
    combined["Latitude"] = pd.to_numeric(combined["Latitude"], errors="coerce")
    combined["Month_dt"] = pd.to_datetime(combined["Month"], format="%Y-%m")
    return combined


def print_summary(df: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {df.shape[1]}")

    print("\nColumns and dtypes:")
    for col in df.columns:
        if col == "Month_dt":
            continue
        print(f"  {col!r}: {df[col].dtype}")

    print("\nMissing values per column:")
    n = len(df)
    missing = df.isna().sum()
    for col in df.columns:
        if col == "Month_dt":
            continue
        # treat empty strings as missing too (CSV blanks read as "" for object dtype)
        blank = (df[col] == "").sum() if df[col].dtype == object else 0
        n_missing = missing[col] + blank
        pct = 100 * n_missing / n
        print(f"  {col:<24} {n_missing:>6} missing ({pct:5.1f}%)")

    print("\nCrime type value counts:")
    print(df["Crime type"].value_counts().to_string())

    print("\nUnique value counts:")
    for col in ["Reported by", "Falls within", "Last outcome category"]:
        print(f"  {col}: {df[col].nunique()} unique values")


def print_quality_flags(df: pd.DataFrame) -> None:
    n = len(df)
    print("\n" + "=" * 70)
    print("DATA QUALITY ISSUES")
    print("=" * 70)

    context_missing = (df["Context"].isna() | (df["Context"] == "")).sum()
    print(f"- 'Context' column: {context_missing}/{n} ({100*context_missing/n:.1f}%) blank "
          "- effectively unusable, always empty in this data source.")

    coord_missing = df["Longitude"].isna() | df["Latitude"].isna()
    print(f"- Missing coordinates (Longitude/Latitude): {coord_missing.sum()}/{n} "
          f"({100*coord_missing.sum()/n:.1f}%) - these are data.police.uk anonymized "
          "'no location identified' crimes.")

    crime_id_missing = (df["Crime ID"].isna() | (df["Crime ID"] == "")).sum()
    print(f"- Missing 'Crime ID': {crime_id_missing}/{n} ({100*crime_id_missing/n:.1f}%) "
          "- expected for anonymized crimes with no ID assigned.")

    outcome_missing = (df["Last outcome category"].isna() | (df["Last outcome category"] == "")).sum()
    print(f"- Missing 'Last outcome category': {outcome_missing}/{n} "
          f"({100*outcome_missing/n:.1f}%) - likely unresolved/recent cases.")

    forces = df["Reported by"].unique()
    print(f"- Single police force only: data covers {list(forces)} - despite the folder "
          "name 'london_crime_2024', this is City of London Police only (the small "
          "financial-district force), NOT the Metropolitan Police / all of Greater London. "
          "Do not interpret this as London-wide crime.")

    dupes = df.duplicated().sum()
    print(f"- Duplicate rows (all columns identical): {dupes}")

    # City of London / Greater London bounding box sanity check
    lon_ok = df["Longitude"].between(-0.6, 0.4)
    lat_ok = df["Latitude"].between(51.2, 51.8)
    has_coords = df["Longitude"].notna() & df["Latitude"].notna()
    outliers = has_coords & ~(lon_ok & lat_ok)
    print(f"- Coordinates outside plausible London bounding box: {outliers.sum()} rows")


def make_crime_types_bar(df: pd.DataFrame) -> None:
    counts = df["Crime type"].value_counts().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    ax.barh(counts.index, counts.values, color=SEQUENTIAL_BLUE, height=0.65)

    ax.set_xlabel("Number of crimes", color=TEXT_SECONDARY)
    ax.set_title("City of London Police: Crimes by Type, 2024", fontsize=13, fontweight="bold")
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(colors=TEXT_SECONDARY)

    for y, v in enumerate(counts.values):
        ax.text(v + max(counts.values) * 0.01, y, f"{v:,}", va="center", fontsize=9, color=TEXT_SECONDARY)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "crime_types_bar.png")
    plt.close(fig)


def make_crime_types_treemap(df: pd.DataFrame) -> None:
    counts = df["Crime type"].value_counts().sort_values(ascending=False)
    total = counts.sum()

    # Magnitude encoding (same job as the bar chart) -> one sequential hue,
    # light to dark by rank, rather than 14 unrelated categorical colors.
    cmap = LinearSegmentedColormap.from_list("seq_blue", ["#cfe1f7", SEQUENTIAL_BLUE])
    colors = [cmap(1 - i / (len(counts) - 1)) for i in range(len(counts))]  # largest = darkest

    fig, ax = plt.subplots(figsize=(12, 7), dpi=150)
    sizes = squarify.normalize_sizes(counts.values, 100, 100)
    rects = squarify.squarify(sizes, 0, 0, 100, 100)

    for rect, label, value, color in zip(rects, counts.index, counts.values, colors):
        ax.add_patch(plt.Rectangle((rect["x"], rect["y"]), rect["dx"], rect["dy"],
                                    facecolor=color, edgecolor="white", linewidth=2))
        # Only label boxes with enough room for readable text.
        if rect["dx"] > 8 and rect["dy"] > 6:
            pct = 100 * value / total
            ax.text(rect["x"] + rect["dx"] / 2, rect["y"] + rect["dy"] / 2 + 1.5,
                    label, ha="center", va="center", fontsize=9, fontweight="bold",
                    color="white" if pct > 6 else TEXT_SECONDARY, wrap=True)
            ax.text(rect["x"] + rect["dx"] / 2, rect["y"] + rect["dy"] / 2 - 2.5,
                    f"{value:,} ({pct:.1f}%)", ha="center", va="center", fontsize=8,
                    color="white" if pct > 6 else TEXT_SECONDARY)

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_title("City of London Police: Crime Type Breakdown, 2024", fontsize=13, fontweight="bold")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "crime_types_treemap.png")
    plt.close(fig)


def make_monthly_trend_total(df: pd.DataFrame) -> None:
    monthly = df.groupby("Month_dt").size().sort_index()

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    ax.plot(monthly.index, monthly.values, color=SEQUENTIAL_BLUE, linewidth=2, marker="o", markersize=5)

    ax.set_ylabel("Number of crimes", color=TEXT_SECONDARY)
    ax.set_title("City of London Police: Total Monthly Crime, 2024", fontsize=13, fontweight="bold")
    ax.set_xticks(monthly.index)
    ax.set_xticklabels(MONTH_LABELS)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors=TEXT_SECONDARY)
    ax.set_ylim(0, monthly.values.max() * 1.15)

    first, last = monthly.index[0], monthly.index[-1]
    ax.annotate(f"{monthly.iloc[0]:,}", (first, monthly.iloc[0]), textcoords="offset points",
                xytext=(-5, 10), fontsize=9, color=TEXT_SECONDARY)
    ax.annotate(f"{monthly.iloc[-1]:,}", (last, monthly.iloc[-1]), textcoords="offset points",
                xytext=(5, 10), fontsize=9, color=TEXT_SECONDARY)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "monthly_trend_total.png")
    plt.close(fig)


def make_monthly_trend_top_types(df: pd.DataFrame, top_n: int = 6) -> None:
    totals = df["Crime type"].value_counts()
    top_types = totals.head(top_n).index.tolist()

    pivot = (
        df.assign(Type=df["Crime type"].where(df["Crime type"].isin(top_types), "Other"))
        .groupby(["Month_dt", "Type"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )
    series_order = top_types + ["Other"]
    pivot = pivot[series_order]

    fig, ax = plt.subplots(figsize=(12, 7), dpi=150)
    colors = CATEGORICAL[:top_n] + [TEXT_SECONDARY]  # "Other" in neutral gray, not a categorical hue
    for label, color in zip(series_order, colors):
        ax.plot(pivot.index, pivot[label], label=label, color=color, linewidth=2,
                marker="o", markersize=4)

    ax.set_ylabel("Number of crimes", color=TEXT_SECONDARY)
    ax.set_title(f"City of London Police: Monthly Trend, Top {top_n} Crime Types, 2024",
                 fontsize=13, fontweight="bold")
    ax.set_xticks(pivot.index)
    ax.set_xticklabels(MONTH_LABELS)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors=TEXT_SECONDARY)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False, fontsize=9)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "monthly_trend_top_types.png")
    plt.close(fig)


def export_geojson(df: pd.DataFrame) -> None:
    has_coords = df["Longitude"].notna() & df["Latitude"].notna()
    n_dropped = (~has_coords).sum()
    geo_df = df.loc[has_coords].drop(columns=["Longitude", "Latitude", "Month_dt"])

    gdf = gpd.GeoDataFrame(
        geo_df,
        geometry=gpd.points_from_xy(df.loc[has_coords, "Longitude"], df.loc[has_coords, "Latitude"]),
        crs="EPSG:4326",
    )

    out_path = OUT_DIR / "london_crime_2024_locations.geojson"
    gdf.to_file(out_path, driver="GeoJSON")

    print("\n" + "=" * 70)
    print("GEOJSON EXPORT")
    print("=" * 70)
    print(f"Wrote {len(gdf)} point features to {out_path}")
    print(f"Excluded {n_dropped} rows with missing coordinates")


def main() -> None:
    df = load_data()
    print_summary(df)
    print_quality_flags(df)

    make_crime_types_bar(df)
    make_crime_types_treemap(df)
    make_monthly_trend_total(df)
    make_monthly_trend_top_types(df)
    export_geojson(df)

    print("\nDone. Charts and GeoJSON written to:", OUT_DIR)


if __name__ == "__main__":
    main()
