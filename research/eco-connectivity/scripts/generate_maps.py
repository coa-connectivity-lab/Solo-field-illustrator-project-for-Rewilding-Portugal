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
    da.attrs = {}  # clear inherited long_name (e.g. "elevation") from upstream .copy(data=...) chains
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
    catchment_rivers = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="coa_catchment_rivers")
    visited = gpd.read_file(config.DATA_PROCESSED / "field_observations.gpkg", layer="visited_sites")

    fig, ax = plt.subplots(figsize=(8, 8))
    study_area.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1)
    catchment_rivers.to_crs(study_area.crs).plot(ax=ax, color="tab:cyan", linewidth=0.6, alpha=0.7,
                                                   label="Traced tributary network (HydroRIVERS)")
    coa_river.to_crs(study_area.crs).plot(ax=ax, color="tab:blue", linewidth=1.5, label="Côa mainstem (OSM)")
    visited.plot(ax=ax, color="tab:red", markersize=25, zorder=5, label="Visited sites (Survey123)")
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title(f"Côa Valley study area (v2: {config.STUDY_AREA_BUFFER_KM:.0f}km mainstem buffer\n"
                 f"+ traced catchment) and visited sites")
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


def map_09_fire_history():
    path = config.DATA_PROCESSED / "covariates" / "fire_last_burn_year.tif"
    da = rioxarray.open_rasterio(path, masked=False).squeeze("band", drop=True)
    da = da.where(da > 0)  # mask never-burned cells so they render as blank, not year-0
    da.name = "last burn year"
    fig, ax = plt.subplots(figsize=(8, 6))
    da.plot(ax=ax, cmap="YlOrRd", add_colorbar=True)
    ax.set_title("Fire history: most recent MODIS-detected burn year, "
                 f"{config.FIRE_HISTORY_START[:4]}–{config.FIRE_HISTORY_END[:4]}\n"
                 "(real MCD64A1 data; blank = no detected burn in this window)")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "09_fire_history.png", dpi=150)
    plt.close(fig)
    print("  wrote 09_fire_history.png")


def map_10_fire_effect():
    no_fire = rioxarray.open_rasterio(
        config.DATA_PROCESSED / "resistance" / "land_resistance_no_fire.tif", masked=True
    ).squeeze("band", drop=True)
    with_fire = rioxarray.open_rasterio(
        config.DATA_PROCESSED / "resistance" / "land_resistance.tif", masked=True
    ).squeeze("band", drop=True)
    diff = with_fire - no_fire
    diff.attrs = {}
    diff.name = "resistance penalty added"
    fig, ax = plt.subplots(figsize=(8, 6))
    diff.plot(ax=ax, cmap="Reds", vmin=0, add_colorbar=True)
    ax.set_title("Land resistance: fire-barrier penalty added on top of the\n"
                 "suitability-derived resistance (0 = unaffected by fire)")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "10_fire_resistance_effect.png", dpi=150)
    plt.close(fig)
    print("  wrote 10_fire_resistance_effect.png")


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

    map_09_fire_history()
    map_10_fire_effect()


if __name__ == "__main__":
    main()
