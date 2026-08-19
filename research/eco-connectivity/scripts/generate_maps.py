"""
generate_maps.py
───────────────────
Numbered PNG maps for the notebook, output/maps/.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import rioxarray

import config

RASTER_DIR = config.OUTPUT_RASTERS
OUT_DIR = config.OUTPUT_MAPS


def _plot_raster(path, title, cmap, vmin=None, vmax=None, out_name=None, cbar_label=""):
    da = rioxarray.open_rasterio(path, masked=True).squeeze("band", drop=True)
    da.name = cbar_label
    fig, ax = plt.subplots(figsize=(8, 6))
    da.plot(ax=ax, cmap=cmap, vmin=vmin, vmax=vmax, add_colorbar=True)
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(OUT_DIR / out_name, dpi=150)
    plt.close(fig)
    print(f"  wrote {out_name}")


def map_01_study_area():
    study_area = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="study_area")
    coa_river = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="coa_river")
    visited = gpd.read_file(config.DATA_PROCESSED / "field_observations.gpkg", layer="visited_sites")

    fig, ax = plt.subplots(figsize=(8, 8))
    study_area.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1)
    coa_river.to_crs(study_area.crs).plot(ax=ax, color="tab:blue", linewidth=1.5)
    visited.plot(ax=ax, color="tab:red", markersize=25, zorder=5)
    ax.set_title(f"Côa Valley study area ({config.STUDY_AREA_BUFFER_KM:.0f}km buffer) and visited sites")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "01_study_area.png", dpi=150)
    plt.close(fig)
    print("  wrote 01_study_area.png")


def map_02_land_tenure():
    study_area = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="study_area")
    reserves = gpd.read_file(config.DATA_PROCESSED / "land_tenure.gpkg", layer="private_reserves")
    hunting = gpd.read_file(config.DATA_PROCESSED / "land_tenure.gpkg", layer="hunting_zones")

    fig, ax = plt.subplots(figsize=(8, 8))
    study_area.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1)
    hunting.plot(ax=ax, column="fig_ord", categorical=True, legend=True, alpha=0.5)
    reserves.plot(ax=ax, facecolor="none", edgecolor="tab:green", linewidth=2)
    ax.set_title("Land tenure: ICNF hunting zones and private reserves (Faia Brava)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "02_land_tenure.png", dpi=150)
    plt.close(fig)
    print("  wrote 02_land_tenure.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    map_01_study_area()
    map_02_land_tenure()

    _plot_raster(RASTER_DIR / "land_normalized_current.tif", "Land connectivity (wolf / wildcat / red deer)",
                 "RdYlBu_r", out_name="03_land_connectivity.png", cbar_label="normalized current")
    _plot_raster(RASTER_DIR / "water_normalized_current.tif", "Water connectivity (otter / native fish / pond turtle)",
                 "RdYlBu_r", out_name="04_water_connectivity.png", cbar_label="normalized current")
    _plot_raster(RASTER_DIR / "air_normalized_current.tif", "Air connectivity (griffon / Egyptian vulture / golden eagle)",
                 "RdYlBu_r", out_name="05_air_connectivity.png", cbar_label="normalized current")
    _plot_raster(RASTER_DIR / "multispecies_mean_connectivity.tif", "Multispecies connectivity (weighted mean)",
                 "RdYlBu_r", out_name="06_multispecies_mean.png", cbar_label="normalized current")
    _plot_raster(RASTER_DIR / "road_tradeoff_class.tif",
                 "Road trade-off: 0=low barrier/low access, 1=conservation priority, 2=compatible access, 3=conflict",
                 "viridis", out_name="07_road_tradeoff.png", cbar_label="trade-off class")
    _plot_raster(RASTER_DIR / "waterway_tradeoff_class.tif",
                 "Waterway trade-off: 0=low barrier/low access, 1=conservation priority, 2=compatible access, 3=conflict",
                 "viridis", out_name="08_waterway_tradeoff.png", cbar_label="trade-off class")


if __name__ == "__main__":
    main()
