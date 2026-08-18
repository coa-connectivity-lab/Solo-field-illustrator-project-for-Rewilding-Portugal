"""
Phase 7: the required diagnostic and final maps, saved as PNGs to
output/maps/. Kept as straightforward static matplotlib/geopandas plots --
maps here are for analysis and validation, not cartographic polish.
"""

import geopandas as gpd
import matplotlib.pyplot as plt

from config import DATA_PROCESSED, GEOPACKAGE_PATH, OUTPUT_MAPS, METRIC_CRS, GEOGRAPHIC_CRS

FIGSIZE = (9, 9)


def savefig(fig, name):
    path = OUTPUT_MAPS / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


def load(name, layer=None):
    return gpd.read_file(DATA_PROCESSED / f"{name}.gpkg", layer=layer or name)


if __name__ == "__main__":
    study_area = load("study_area")
    buildings = gpd.read_file(GEOPACKAGE_PATH, layer="apartment_buildings")
    municipalities = load("candidate_municipalities" if (DATA_PROCESSED / "candidate_municipalities.gpkg").exists() else "study_area", layer="municipalities" if (DATA_PROCESSED / "candidate_municipalities.gpkg").exists() else None)

    # Building footprints (10-30m) are invisible at the scale of a ~90km-wide
    # study area, and geopandas' markersize only applies to point geometry
    # anyway -- plot centroids for every building overlay below, keeping the
    # actual footprint polygons only in the GeoPackage itself.
    buildings_pts = buildings.copy()
    buildings_pts["geometry"] = buildings.to_crs(METRIC_CRS).geometry.centroid
    buildings_pts = buildings_pts.set_geometry("geometry").set_crs(METRIC_CRS, allow_override=True).to_crs(GEOGRAPHIC_CRS)

    # 1. Study area -------------------------------------------------------
    fig, ax = plt.subplots(figsize=FIGSIZE)
    municipalities.boundary.plot(ax=ax, color="grey", linewidth=0.8, linestyle="--")
    study_area.boundary.plot(ax=ax, color="black", linewidth=2)
    ax.set_title("Study area: Guarda + Pinhel + Vila Nova de Foz Coa\n(dashed: all candidate municipalities checked)")
    savefig(fig, "01_study_area.png")

    # 2. Apartment buildings -----------------------------------------------
    fig, ax = plt.subplots(figsize=FIGSIZE)
    study_area.boundary.plot(ax=ax, color="black", linewidth=1)
    buildings_pts.plot(ax=ax, color="crimson", markersize=8)
    ax.set_title(f"Apartment buildings (n={len(buildings)})")
    savefig(fig, "02_apartment_buildings.png")

    # 3. Nature areas / parks -----------------------------------------------
    nature = load("nature_areas")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    study_area.boundary.plot(ax=ax, color="black", linewidth=1)
    nature.plot(ax=ax, color="forestgreen", alpha=0.5)
    buildings_pts.plot(ax=ax, color="crimson", markersize=4)
    ax.set_title("Nature and recreation areas (parks, forests, protected areas)")
    savefig(fig, "03_nature_areas.png")

    # 4. Coa river ------------------------------------------------------------
    river = load("coa_river")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    study_area.boundary.plot(ax=ax, color="black", linewidth=1)
    river.plot(ax=ax, color="royalblue", linewidth=2)
    buildings_pts.plot(ax=ax, color="crimson", markersize=4)
    ax.set_title("Rio Coa (named segments only) and apartment buildings")
    savefig(fig, "04_coa_river.png")

    # 5. Major amenities --------------------------------------------------
    amenities = load("amenities")
    parking = load("parking")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    study_area.boundary.plot(ax=ax, color="black", linewidth=1)
    amenities.plot(ax=ax, color="darkorange", markersize=10, label="amenities")
    parking.plot(ax=ax, color="slategrey", markersize=10, label="parking")
    buildings_pts.plot(ax=ax, color="crimson", markersize=4, label="apartment buildings")
    ax.set_title("Everyday amenities and mapped parking")
    ax.legend()
    savefig(fig, "05_amenities.png")

    # 6. Final livability score choropleth -----------------------------------
    fig, ax = plt.subplots(figsize=FIGSIZE)
    study_area.boundary.plot(ax=ax, color="black", linewidth=1)
    buildings_pts.plot(ax=ax, column="livability_score", cmap="RdYlGn", markersize=25, legend=True,
                    vmin=0, vmax=100)
    ax.set_title("Apartment-building livability score (0-100)")
    savefig(fig, "06_livability_score.png")

    # 7. High-ranking apartment buildings -------------------------------------
    top_n = 20
    top_buildings = buildings_pts.nsmallest(top_n, "livability_rank")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    study_area.boundary.plot(ax=ax, color="black", linewidth=1)
    buildings_pts.plot(ax=ax, color="lightgrey", markersize=6)
    top_buildings.plot(ax=ax, color="darkgreen", markersize=40, edgecolor="black")
    ax.set_title(f"Top {top_n} highest-ranked apartment buildings")
    savefig(fig, "07_top_ranked_buildings.png")

    print("\nAll 7 maps generated.")
