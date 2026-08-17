"""
Theft hotspot mapping for the City of London Police 2024 street-level crime
data (data/london_crime_2024/YYYY-MM/*.csv), using Getis-Ord Gi* local
statistics on LSOA polygons, per the methodology in documents/hotspots.pdf
(NIJ "Mapping Crime: Understanding Hot Spots").

SCOPE CAVEAT: this dataset is City of London Police only (the small
financial-district force), NOT the Metropolitan Police / Greater London.
Theft here = {Other theft, Theft from the person, Shoplifting, Bicycle theft}.

Outputs (written next to this script):
  - theft_gi_star_rate.png        Gi* hotspots, theft rate per 1,000 residents
  - theft_gi_star_raw.png         Gi* hotspots, raw theft counts (companion)
  - theft_kde_density.png         continuous KDE surface of theft points
  - theft_hotspots_map.html       self-contained folium map, rate + raw layers
  - theft_hotspot_lsoa_summary.csv  ranked LSOA table (counts, rate, Gi* Zs)

External data is cached under external/ on first run:
  - lsoa_boundaries_mesh.geojson  LSOA polygons covering City of London + a
                                   900m buffer into bordering boroughs, from
                                   the ONS Open Geography Portal.
  - lsoa_population_2021.csv      Census 2021 usual-resident population per
                                   LSOA (table TS001), from the Nomis API.

Run with:
  /home/linda/anaconda3/envs/claude_code_workshop/bin/python hotspots_london_crime_2024.py
"""

from pathlib import Path

import esda
import folium
import geopandas as gpd
import libpysal
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde

DATA_DIR = Path(__file__).resolve().parent.parent / "london_crime_2024"
OUT_DIR = Path(__file__).resolve().parent
EXTERNAL_DIR = OUT_DIR / "external"

THEFT_TYPES = ["Other theft", "Theft from the person", "Shoplifting", "Bicycle theft"]
POP_FLOOR = 100  # minimum denominator for rate calc, flags near-zero-resident LSOAs

ONS_LSOA_FEATURESERVER = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V10/FeatureServer/0/query"
)
NOMIS_TS001_URL = "https://www.nomisweb.co.uk/api/v01/dataset/NM_2021_1.data.csv"
MESH_BUFFER_M = 900

# dataviz-skill palette (references/palette.md)
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7", "#e34948"]
SEQUENTIAL_BLUE = "#2a78d6"
GRID_COLOR = "#d9d9d6"
TEXT_SECONDARY = "#52514e"

# Diverging pair (blue <-> red), neutral gray midpoint, 3 steps per arm -
# matches the standard 7-bin ArcGIS Gi* classification.
GI_STAR_BINS = [
    ("Cold Spot 99%", "#0d366b"),
    ("Cold Spot 95%", "#256abf"),
    ("Cold Spot 90%", "#6da7ec"),
    ("Not Significant", GRID_COLOR),
    ("Hot Spot 90%", "#f2a9a0"),
    ("Hot Spot 95%", "#e34948"),
    ("Hot Spot 99%", "#7a1f1e"),
]
GI_STAR_LABELS = [b[0] for b in GI_STAR_BINS]
GI_STAR_COLORS = [b[1] for b in GI_STAR_BINS]
GI_STAR_EDGES = [-np.inf, -2.58, -1.96, -1.65, 1.65, 1.96, 2.58, np.inf]

CAVEAT_TEXT = (
    "City of London Police data only (not Greater London / Met Police)  |  "
    "Theft = Other theft, Theft from the person, Shoplifting, Bicycle theft  |  "
    "Mesh includes neighboring-borough LSOAs for spatial context"
)


def classify_gi_star(z: pd.Series) -> pd.Series:
    return pd.cut(z, bins=GI_STAR_EDGES, labels=GI_STAR_LABELS)


def load_theft_points() -> gpd.GeoDataFrame:
    files = sorted(DATA_DIR.glob("*/*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found under {DATA_DIR}")

    frames = [pd.read_csv(f, dtype=str) for f in files]
    df = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(df)} total crime records from {len(files)} monthly files.")

    theft = df[df["Crime type"].isin(THEFT_TYPES)].copy()
    print(f"Theft records ({', '.join(THEFT_TYPES)}): {len(theft)}")

    theft["Longitude"] = pd.to_numeric(theft["Longitude"], errors="coerce")
    theft["Latitude"] = pd.to_numeric(theft["Latitude"], errors="coerce")
    has_coords = theft["Longitude"].notna() & theft["Latitude"].notna()
    n_dropped = (~has_coords).sum()
    print(f"Dropping {n_dropped}/{len(theft)} ({100*n_dropped/len(theft):.1f}%) theft "
          "records with no geocoded location (data.police.uk anonymized crimes).")
    theft = theft.loc[has_coords].copy()

    gdf = gpd.GeoDataFrame(
        theft,
        geometry=gpd.points_from_xy(theft["Longitude"], theft["Latitude"]),
        crs="EPSG:4326",
    )
    return gdf


def load_mesh() -> gpd.GeoDataFrame:
    cache_path = EXTERNAL_DIR / "lsoa_boundaries_mesh.geojson"
    if cache_path.exists():
        print(f"Loading cached LSOA mesh from {cache_path}")
        return gpd.read_file(cache_path)

    print("Fetching City of London core LSOAs from ONS FeatureServer...")
    core_resp = requests.get(
        ONS_LSOA_FEATURESERVER,
        params={
            "where": "LSOA21NM LIKE 'City of London%'",
            "outFields": "*",
            "f": "geojson",
        },
        timeout=30,
    )
    core_resp.raise_for_status()
    core = gpd.GeoDataFrame.from_features(core_resp.json()["features"], crs="EPSG:4326")
    print(f"  Core LSOAs found: {len(core)}")

    core_bng = core.to_crs(epsg=27700)
    buffer_geom = core_bng.dissolve().buffer(MESH_BUFFER_M).iloc[0]
    buffer_wgs84 = gpd.GeoSeries([buffer_geom], crs=27700).to_crs(epsg=4326)
    minx, miny, maxx, maxy = buffer_wgs84.total_bounds

    print(f"Fetching LSOAs within {MESH_BUFFER_M}m buffer envelope from ONS...")
    cand_resp = requests.get(
        ONS_LSOA_FEATURESERVER,
        params={
            "geometry": f"{minx},{miny},{maxx},{maxy}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "f": "geojson",
        },
        timeout=30,
    )
    cand_resp.raise_for_status()
    candidates = gpd.GeoDataFrame.from_features(cand_resp.json()["features"], crs="EPSG:4326")

    cand_bng = candidates.to_crs(epsg=27700)
    mesh = candidates.loc[cand_bng.geometry.intersects(buffer_geom)].reset_index(drop=True)

    boroughs = sorted(mesh["LSOA21NM"].str.extract(r"^(.*?) \d")[0].unique())
    print(f"  Mesh size: {len(mesh)} LSOAs across {len(boroughs)} boroughs: {', '.join(boroughs)}")

    EXTERNAL_DIR.mkdir(exist_ok=True)
    mesh.to_file(cache_path, driver="GeoJSON")
    print(f"  Cached to {cache_path}")
    return mesh


def load_population(lsoa_codes: list[str]) -> pd.DataFrame:
    cache_path = EXTERNAL_DIR / "lsoa_population_2021.csv"
    if cache_path.exists():
        print(f"Loading cached population data from {cache_path}")
        return pd.read_csv(cache_path)

    print("Fetching Census 2021 usual-resident population (TS001) from Nomis API...")
    resp = requests.get(
        NOMIS_TS001_URL,
        params={"geography": ",".join(lsoa_codes), "measures": "20100"},
        timeout=30,
    )
    resp.raise_for_status()
    raw = pd.read_csv(pd.io.common.StringIO(resp.text))
    total = raw[raw["C2021_RESTYPE_3_CODE"] == "0"][
        ["GEOGRAPHY_CODE", "GEOGRAPHY_NAME", "OBS_VALUE"]
    ].rename(columns={
        "GEOGRAPHY_CODE": "lsoa_code",
        "GEOGRAPHY_NAME": "lsoa_name",
        "OBS_VALUE": "population_2021",
    })
    print(f"  Population rows: {len(total)}")

    EXTERNAL_DIR.mkdir(exist_ok=True)
    total.to_csv(cache_path, index=False)
    print(f"  Cached to {cache_path}")
    return total


def filter_to_mesh(points: gpd.GeoDataFrame, mesh: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    mesh_codes = set(mesh["LSOA21CD"])
    in_mesh = points["LSOA code"].isin(mesh_codes)
    n_dropped = (~in_mesh).sum()
    print(f"Theft records outside the LSOA mesh: {n_dropped}/{len(points)} "
          f"({100*n_dropped/len(points):.2f}%) - dropped.")
    return points.loc[in_mesh].copy()


def build_lsoa_gdf(points: gpd.GeoDataFrame, mesh: gpd.GeoDataFrame, population: pd.DataFrame) -> gpd.GeoDataFrame:
    counts = points.groupby("LSOA code").size().rename("theft_count")

    lsoa = mesh[["LSOA21CD", "LSOA21NM", "geometry"]].rename(
        columns={"LSOA21CD": "lsoa_code", "LSOA21NM": "lsoa_name"}
    )
    lsoa = lsoa.merge(counts, left_on="lsoa_code", right_index=True, how="left")
    lsoa["theft_count"] = lsoa["theft_count"].fillna(0).astype(int)

    lsoa = lsoa.merge(population[["lsoa_code", "population_2021"]], on="lsoa_code", how="left")
    missing_pop = lsoa["population_2021"].isna().sum()
    if missing_pop:
        raise ValueError(f"{missing_pop} mesh LSOAs have no population value - code mismatch.")

    lsoa["pop_floor_applied"] = lsoa["population_2021"] < POP_FLOOR
    denom = lsoa["population_2021"].clip(lower=POP_FLOOR)
    lsoa["theft_rate_per_1000"] = lsoa["theft_count"] / denom * 1000

    n_floored = lsoa["pop_floor_applied"].sum()
    print(f"LSOAs with population < {POP_FLOOR} (rate floored, flagged): {n_floored}")

    return lsoa.reset_index(drop=True)


def build_spatial_weights(lsoa: gpd.GeoDataFrame) -> libpysal.weights.W:
    w = libpysal.weights.Queen.from_dataframe(lsoa, use_index=False)
    n_islands = len(w.islands)
    print(f"Queen contiguity weights: {w.n} units, {n_islands} islands.")
    if n_islands:
        knn = libpysal.weights.KNN.from_dataframe(lsoa, k=1)
        w = libpysal.weights.util.attach_islands(w, knn)
        print(f"  Attached {n_islands} island(s) via nearest-neighbor fallback. "
              f"Remaining islands: {len(w.islands)}")
    w.transform = "r"
    return w


def compute_gi_star(lsoa: gpd.GeoDataFrame, w: libpysal.weights.W, value_col: str, prefix: str) -> None:
    # esda's permutation inference silently degenerates (all p_sim == 1/(perms+1))
    # when given an int64 array - always pass float64.
    y = lsoa[value_col].to_numpy().astype(float)
    gi = esda.getisord.G_Local(y, w, star=True, permutations=999, seed=42)

    lsoa[f"{prefix}_zscore"] = gi.Zs
    lsoa[f"{prefix}_p_sim"] = gi.p_sim
    lsoa[f"{prefix}_category"] = classify_gi_star(pd.Series(gi.Zs))

    sig_permutation = gi.p_sim < 0.05
    sig_zscore = lsoa[f"{prefix}_category"] != "Not Significant"
    disagree = (sig_permutation != sig_zscore).sum()
    print(f"Gi* ({prefix}): {sig_zscore.sum()} significant by Z-score threshold, "
          f"{sig_permutation.sum()} by permutation p<0.05, {disagree} disagree.")


def make_gi_star_map(lsoa: gpd.GeoDataFrame, prefix: str, title: str, out_path: Path) -> None:
    cmap = ListedColormap(GI_STAR_COLORS)
    norm = BoundaryNorm(range(len(GI_STAR_COLORS) + 1), cmap.N)
    codes = lsoa[f"{prefix}_category"].map({label: i for i, label in enumerate(GI_STAR_LABELS)})

    fig, ax = plt.subplots(figsize=(10, 9), dpi=150)
    lsoa.assign(_code=codes).plot(
        column="_code", cmap=cmap, norm=norm, ax=ax, edgecolor="white", linewidth=0.4
    )

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_axis_off()
    ax.text(0.5, -0.03, CAVEAT_TEXT, transform=ax.transAxes, ha="center", va="top",
            fontsize=7.5, color=TEXT_SECONDARY, wrap=True)

    legend_handles = [Patch(facecolor=c, edgecolor="white", label=l)
                       for l, c in zip(GI_STAR_LABELS, GI_STAR_COLORS)]
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.0, 1.0),
              frameon=False, fontsize=9, title="Gi* Category")

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def make_kde_density(points: gpd.GeoDataFrame, lsoa: gpd.GeoDataFrame, out_path: Path) -> None:
    points_bng = points.to_crs(epsg=27700)
    lsoa_bng = lsoa.to_crs(epsg=27700)

    xy = np.vstack([points_bng.geometry.x, points_bng.geometry.y])
    kde = gaussian_kde(xy)

    minx, miny, maxx, maxy = lsoa_bng.total_bounds
    pad = 300
    xx, yy = np.mgrid[minx - pad:maxx + pad:200j, miny - pad:maxy + pad:200j]
    positions = np.vstack([xx.ravel(), yy.ravel()])
    density = kde(positions).reshape(xx.shape)

    cmap = plt.cm.colors.LinearSegmentedColormap.from_list(
        "seq_blue", ["#fcfcfb", "#cde2fb", SEQUENTIAL_BLUE, "#0d366b"]
    )

    fig, ax = plt.subplots(figsize=(10, 9), dpi=150)
    ax.contourf(xx, yy, density, levels=15, cmap=cmap)
    lsoa_bng.boundary.plot(ax=ax, color=GRID_COLOR, linewidth=0.5)
    points_bng.plot(ax=ax, markersize=2, color=TEXT_SECONDARY, alpha=0.25)

    ax.set_title("City of London Police: Theft Density (KDE), 2024", fontsize=13, fontweight="bold")
    ax.set_axis_off()
    ax.text(0.5, -0.03, CAVEAT_TEXT, transform=ax.transAxes, ha="center", va="top",
            fontsize=7.5, color=TEXT_SECONDARY, wrap=True)

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def make_folium_map(lsoa: gpd.GeoDataFrame, out_path: Path) -> None:
    lsoa_wgs84 = lsoa.to_crs(epsg=4326)
    centroid = lsoa_wgs84.geometry.union_all().centroid
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=14, tiles="CartoDB positron")

    color_map = dict(zip(GI_STAR_LABELS, GI_STAR_COLORS))

    for prefix, layer_name, default_show in [
        ("rate", "Gi* Hotspots - Theft Rate per 1,000", True),
        ("raw", "Gi* Hotspots - Raw Theft Count", False),
    ]:
        fg = folium.FeatureGroup(name=layer_name, show=default_show)
        for _, row in lsoa_wgs84.iterrows():
            popup_html = (
                f"<b>{row['lsoa_name']}</b> ({row['lsoa_code']})<br>"
                f"Population (2021): {row['population_2021']:,.0f}"
                f"{' <i>(floored)</i>' if row['pop_floor_applied'] else ''}<br>"
                f"Theft count: {row['theft_count']}<br>"
                f"Theft rate /1,000: {row['theft_rate_per_1000']:.2f}<br>"
                f"Gi* Z-score ({prefix}): {row[f'{prefix}_zscore']:.2f}<br>"
                f"Category ({prefix}): {row[f'{prefix}_category']}"
            )
            folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=lambda _f, cat=row[f"{prefix}_category"]: {
                    "fillColor": color_map[cat],
                    "color": "white",
                    "weight": 0.6,
                    "fillOpacity": 0.75,
                },
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(fg)
        fg.add_to(m)

    legend_rows = "".join(
        f'<div><span style="background:{c};width:12px;height:12px;'
        f'display:inline-block;margin-right:6px;"></span>{l}</div>'
        for l, c in zip(GI_STAR_LABELS, GI_STAR_COLORS)
    )
    legend_html = f"""
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 10px 12px; border: 1px solid #c3c2b7;
                border-radius: 4px; font-size: 12px; font-family: sans-serif;">
      <b>Gi* Category</b>{legend_rows}
      <div style="margin-top:6px; max-width: 260px; font-size: 10px; color: {TEXT_SECONDARY};">
        {CAVEAT_TEXT}
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)

    m.save(str(out_path))
    print(f"Wrote {out_path}")


def export_summary_csv(lsoa: gpd.GeoDataFrame, out_path: Path) -> None:
    summary = lsoa.drop(columns="geometry").sort_values("rate_zscore", ascending=False)
    summary.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")


def main() -> None:
    points = load_theft_points()
    mesh = load_mesh()
    population = load_population(sorted(mesh["LSOA21CD"].unique()))
    points = filter_to_mesh(points, mesh)

    lsoa = build_lsoa_gdf(points, mesh, population)
    w = build_spatial_weights(lsoa)

    compute_gi_star(lsoa, w, "theft_rate_per_1000", "rate")
    compute_gi_star(lsoa, w, "theft_count", "raw")

    make_gi_star_map(
        lsoa, "rate",
        "City of London Police: Theft Hotspots, 2024 (Gi* on Rate per 1,000 Residents)",
        OUT_DIR / "theft_gi_star_rate.png",
    )
    make_gi_star_map(
        lsoa, "raw",
        "City of London Police: Theft Hotspots, 2024 (Gi* on Raw Counts)",
        OUT_DIR / "theft_gi_star_raw.png",
    )
    make_kde_density(points, lsoa, OUT_DIR / "theft_kde_density.png")
    make_folium_map(lsoa, OUT_DIR / "theft_hotspots_map.html")
    export_summary_csv(lsoa, OUT_DIR / "theft_hotspot_lsoa_summary.csv")

    print("\nDone. Outputs written to:", OUT_DIR)


if __name__ == "__main__":
    main()
