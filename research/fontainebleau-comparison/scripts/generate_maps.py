"""
generate_maps.py
────────────────────
Three report-embedded PNG maps, output/maps/ - matplotlib/geopandas, same
convention as research/eco-connectivity/scripts/generate_maps.py,
research/camargue-comparison/, and research/limpopo-mine-restoration/.

All maps in CRS_METRIC (EPSG:2154, RGF93/Lambert-93).
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import config

config.OUTPUT_MAPS.mkdir(parents=True, exist_ok=True)


def _load(gpkg, layer):
    return gpd.read_file(gpkg, layer=layer).to_crs(config.CRS_METRIC)


def _base(ax, boundary):
    boundary.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1.3, zorder=1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def map_01_protected_areas():
    boundary = _load(config.BOUNDARY_GPKG, "fontainebleau_boundary")
    pa = _load(config.PROTECTED_GPKG, "protected_areas")

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary)

    designation_colors = {
        "UNESCO Biosphere Reserve": "#762a83",
        "Regional Nature Park": "#1b7837",
        "State Forest (ONF)": "#5aae61",
        "Réserve Biologique Intégrale (strict reserve)": "#d73027",
        "Réserve Biologique Dirigée (managed reserve)": "#fdae61",
    }
    for designation, color in designation_colors.items():
        subset = pa[pa["designation"] == designation]
        if not subset.empty:
            alpha = 0.15 if designation in ("UNESCO Biosphere Reserve", "Regional Nature Park") else 0.7
            subset.plot(ax=ax, facecolor=color, edgecolor=color, alpha=alpha, linewidth=1.0, zorder=2)

    ax.set_title("Map 1 — Fontainebleau protected-area context\n"
                  "Forest boundary, biosphere reserve, regional park, and the Réserve Biologique network",
                  fontsize=12, weight="bold")
    handles = [Patch(facecolor=c, edgecolor=c, alpha=(0.3 if d in ("UNESCO Biosphere Reserve", "Regional Nature Park") else 0.8), label=d)
               for d, c in designation_colors.items()]
    ax.legend(handles=handles, loc="lower left", fontsize=6.5, framealpha=0.9)
    ax.text(0.99, 0.01, "CRS: EPSG:2154 (RGF93/Lambert-93) | Sources: OSM (Overpass), Wikidata",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color="#555555")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_MAPS / "01_protected_areas.png", dpi=150)
    plt.close(fig)
    print("  wrote 01_protected_areas.png")


def map_02_species_occurrences():
    boundary = _load(config.BOUNDARY_GPKG, "fontainebleau_boundary")
    pa = _load(config.PROTECTED_GPKG, "protected_areas")
    sp = _load(config.SPECIES_GPKG, "occurrences")

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary)
    rbi = pa[pa["designation"].str.contains("Intégrale", na=False)]
    rbi.plot(ax=ax, facecolor="#cccccc", edgecolor="#888888", alpha=0.5, linewidth=0.6, zorder=1)

    group_colors = {
        "mammal": "#b35806", "bird": "#2166ac", "reptile (Squamata only - see module docstring)": "#1a9850",
        "amphibian": "#66c2a5", "insect": "#f46d43", "vascular plant": "#762a83",
    }
    group_labels = {
        "mammal": "Mammal", "bird": "Bird", "reptile (Squamata only - see module docstring)": "Reptile (Squamata)",
        "amphibian": "Amphibian", "insect": "Insect", "vascular plant": "Vascular plant",
    }
    for group, color in group_colors.items():
        subset = sp[sp["group"] == group]
        if not subset.empty:
            subset.plot(ax=ax, color=color, markersize=14, zorder=3, alpha=0.8, label=group_labels[group])

    ax.set_title(f"Map 2 — Species occurrences by taxonomic group (GBIF, n={len(sp)})\n"
                  "Grey: Réserves Biologiques Intégrales (strict reserves)",
                  fontsize=12, weight="bold")
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=7, label=group_labels[g])
               for g, c in group_colors.items()]
    ax.legend(handles=handles, loc="lower left", fontsize=7, framealpha=0.9)
    ax.text(0.99, 0.01, "GBIF live bbox search, taxonKey-filtered, 300-record cap per group - a screening "
                        "sample, not a complete inventory (see report Limitations)",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color="#555555")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_MAPS / "02_species_occurrences.png", dpi=150)
    plt.close(fig)
    print("  wrote 02_species_occurrences.png")


def map_03_ecotourism_facilities():
    boundary = _load(config.BOUNDARY_GPKG, "fontainebleau_boundary")
    pa = _load(config.PROTECTED_GPKG, "protected_areas")
    fac = _load(config.FACILITIES_GPKG, "facilities")

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary)
    rbi = pa[pa["designation"].str.contains("Intégrale", na=False)]
    rbi.plot(ax=ax, facecolor="#d73027", edgecolor="#d73027", alpha=0.25, linewidth=0.8, zorder=1)

    climbing = fac[fac["facility_type"] == "climbing_area"]
    trail_info = fac[fac["facility_type"] == "trail_information_point"]
    parking = fac[fac["facility_type"] == "parking"]

    climbing.plot(ax=ax, color="#762a83", markersize=6, alpha=0.5, zorder=2, label="Climbing/bouldering area")
    trail_info.plot(ax=ax, color="#4575b4", markersize=8, alpha=0.6, zorder=3, label="Trail information point")
    parking.plot(ax=ax, color="#333333", markersize=40, marker="s", zorder=4, label="Named parking")

    ax.set_title(f"Map 3 — Ecotourism access & facilities (n={len(fac)})\n"
                  f"{len(climbing)} climbing/bouldering features, {len(trail_info)} trail information points",
                  fontsize=12, weight="bold")
    handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#762a83", markersize=6, alpha=0.7, label="Climbing/bouldering area"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#4575b4", markersize=6, alpha=0.7, label="Trail information point"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#333333", markersize=8, label="Named parking"),
        Patch(facecolor="#d73027", edgecolor="#d73027", alpha=0.25, label="Réserve Biologique Intégrale (strict reserve)"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7, framealpha=0.9)
    ax.text(0.99, 0.01, "Facility density itself is the visitor-pressure signal this map is built to show "
                        "- see report §7",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color="#555555")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_MAPS / "03_ecotourism_facilities.png", dpi=150)
    plt.close(fig)
    print("  wrote 03_ecotourism_facilities.png")


def main():
    map_01_protected_areas()
    map_02_species_occurrences()
    map_03_ecotourism_facilities()


if __name__ == "__main__":
    main()
