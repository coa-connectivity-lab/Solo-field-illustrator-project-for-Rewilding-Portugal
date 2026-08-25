"""
generate_maps.py
─────────────────────
One report-embedded PNG map: off-road/track network density plus the three
Guarda-to-rewilding-site routes, each labeled with distance/time/ruggedness.
Same matplotlib/geopandas convention as the other research/*-comparison/
scripts/generate_maps.py modules.

All maps in CRS_METRIC (EPSG:3763, ETRS89/Portugal TM06).
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.geometry import Point

import config

DEST_COLORS = {
    "Faia Brava": "#1a9850",
    "Vale Carapito": "#4575b4",
    "Ermo das Águias": "#d73027",
}


def map_01_guarda_access():
    tracks = gpd.read_file(config.ROUTES_GPKG, layer="offroad_tracks").to_crs(config.CRS_METRIC)
    routes = gpd.read_file(config.ROUTES_GPKG, layer="guarda_routes").to_crs(config.CRS_METRIC)
    origin_pt = gpd.GeoSeries([Point(config.ORIGIN["lon"], config.ORIGIN["lat"])],
                               crs=config.CRS_DISPLAY).to_crs(config.CRS_METRIC).iloc[0]

    fig, ax = plt.subplots(figsize=(10, 10))
    tracks.plot(ax=ax, color="#bbbbbb", linewidth=0.3, alpha=0.6, zorder=1)

    for _, row in routes.iterrows():
        color = DEST_COLORS.get(row["destination"], "#333333")
        row_geom = gpd.GeoSeries([row.geometry], crs=config.CRS_METRIC)
        row_geom.plot(ax=ax, color=color, linewidth=2.5, zorder=3)

    ax.scatter([origin_pt.x], [origin_pt.y], color="black", marker="s", s=80, zorder=5)
    ax.annotate(config.ORIGIN["name"], (origin_pt.x, origin_pt.y), fontsize=9, weight="bold",
                xytext=(8, 8), textcoords="offset points", zorder=6)

    for _, row in routes.iterrows():
        end = row.geometry.coords[-1]
        color = DEST_COLORS.get(row["destination"], "#333333")
        ax.scatter([end[0]], [end[1]], color=color, marker="o", s=60, zorder=5,
                   edgecolor="black", linewidth=0.6)
        label = (f"{row['destination']}\n{row['drive_distance_km']:.0f} km, "
                 f"{row['drive_time_min']:.0f} min\n{row['unpaved_fraction']*100:.0f}% unpaved-adjacent")
        ax.annotate(label, (end[0], end[1]), fontsize=7.5, ha="left",
                    xytext=(8, -6), textcoords="offset points", zorder=6,
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor=color, linewidth=0.8))

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title("Guarda → rewilding-site visitor access\n"
                  "Off-road/track network density (grey) and driving routes to the 3 sites",
                  fontsize=13, weight="bold")
    handles = [
        Line2D([0], [0], color="#bbbbbb", linewidth=2, label="Off-road/unpaved track (OSM)"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="black", markersize=9, label=config.ORIGIN["name"]),
    ] + [
        Line2D([0], [0], color=c, linewidth=2.5, label=f"Route to {name}")
        for name, c in DEST_COLORS.items()
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7.5, framealpha=0.9)
    ax.text(0.99, 0.01,
            "CRS: EPSG:3763 | Routes: OpenRouteService | Tracks: OSM (Overpass)\n"
            "Ruggedness = % of route within 60m of an acquired unpaved track",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color="#555555")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_MAPS / "01_guarda_access.png", dpi=150)
    plt.close(fig)
    print("  wrote 01_guarda_access.png")


def main():
    map_01_guarda_access()


if __name__ == "__main__":
    main()
