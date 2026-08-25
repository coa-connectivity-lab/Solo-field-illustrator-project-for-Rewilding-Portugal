"""
generate_maps.py
────────────────────
Report-embedded PNG maps, output/maps/ — follows this project's own
established convention for report-ready static maps (matplotlib/geopandas,
confirmed by reading research/eco-connectivity/scripts/generate_maps.py; not
QGIS print layouts, which this project doesn't use for this purpose).

All maps rendered in CRS_METRIC (ESRI:102022, Africa Albers Equal Area
Conic) so distances/areas read consistently across all of them.

v6 addition: map_00_limpopo_at_a_glance() - a single combined "at a glance"
summary figure (notebook v6 lead image for this region's mine-restoration/
connectivity subsection), condensing Map 4's restoration-priority finding.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import config

config.OUTPUT_MAPS.mkdir(parents=True, exist_ok=True)


def _load(gpkg, layer):
    return gpd.read_file(gpkg, layer=layer).to_crs(config.CRS_METRIC)


def _base(ax, boundary, rivers=None):
    boundary.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1.3, zorder=1)
    if rivers is not None:
        rivers.plot(ax=ax, color="#9ecae1", linewidth=0.3, alpha=0.7, zorder=0)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def map_00_limpopo_at_a_glance():
    """Condenses Map 4's restoration-priority finding into one figure:
    documented TFCA context, and the mines closest to protected areas
    (priority vs. secondary restoration opportunities)."""
    boundary = _load(config.BOUNDARY_GPKG, "limpopo_boundary")
    pa = _load(config.PROTECTED_GPKG, "protected_areas")
    documented = _load(config.CONNECTIVITY_GPKG, "documented_tfca_context")
    pinch = _load(config.CONNECTIVITY_GPKG, "mine_pinch_points")

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary)

    pa_poly = pa[pa["boundary_type"] == "polygon (OSM)"]
    pa_poly.plot(ax=ax, facecolor="#cccccc", edgecolor="#888888", alpha=0.4, linewidth=0.8, zorder=1)
    documented.plot(ax=ax, facecolor="#1a9850", edgecolor="#1a9850", alpha=0.35, linewidth=1.5, zorder=2)

    high_priority = pinch[pinch["distance_km"] <= 5.0]
    lower_priority = pinch[pinch["distance_km"] > 5.0]
    lower_priority.plot(ax=ax, color="#fee08b", markersize=30, marker="o", zorder=3,
                         edgecolor="black", linewidth=0.4)
    high_priority.plot(ax=ax, color="#d73027", markersize=55, marker="*", zorder=4,
                        edgecolor="black", linewidth=0.5)

    ax.set_title("Limpopo at a glance\n"
                  f"{len(high_priority)} priority mine-restoration/connectivity opportunities identified",
                  fontsize=13, weight="bold", loc="left")
    ax.text(0.01, 0.01,
            "Key implication: mines closest to protected areas are where\n"
            "restoration could plausibly contribute to landscape\n"
            "connectivity - proximity only, not a validated ecological\n"
            "assessment (see report §7).",
            transform=ax.transAxes, fontsize=8, ha="left", va="bottom",
            style="italic", color="#333333",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="#cccccc"))
    handles = [
        Line2D([0], [0], marker="*", color="w", markerfacecolor="#d73027", markeredgecolor="black",
               markersize=14, label="Priority (mine <= 5 km from a protected area)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#fee08b", markeredgecolor="black",
               markersize=9, label="Secondary (mine 5-10 km from a protected area)"),
        Patch(facecolor="#1a9850", edgecolor="#1a9850", alpha=0.35, label="Documented TFCA context (GLTFCA/GMTFCA)"),
        Patch(facecolor="#cccccc", edgecolor="#888888", alpha=0.4, label="Other protected area"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=7.5, framealpha=0.9)
    ax.text(0.99, 0.01, "CRS: ESRI:102022 (Africa Albers Equal Area Conic) | Sources: OSM, Wikidata",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color="#555555")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_MAPS / "00_limpopo_at_a_glance.png", dpi=150)
    plt.close(fig)
    print(f"  wrote 00_limpopo_at_a_glance.png ({len(high_priority)} priority + {len(lower_priority)} secondary)")


def map_01_regional_context():
    boundary = _load(config.BOUNDARY_GPKG, "limpopo_boundary")
    rivers = _load(config.RIVERS_GPKG, "rivers")
    pa = _load(config.PROTECTED_GPKG, "protected_areas")
    mines = _load(config.MINING_GPKG, "mining_sites")

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary, rivers)

    pa_poly = pa[pa["boundary_type"] == "polygon (OSM)"]
    pa_point = pa[pa["boundary_type"] != "polygon (OSM)"]
    pa_poly.plot(ax=ax, facecolor="#1a9850", edgecolor="#1a9850", alpha=0.35, linewidth=1.2,
                 zorder=2, label="Major protected area (real boundary)")
    pa_point.plot(ax=ax, color="#4575b4", markersize=10, zorder=3, label="Protected area (Wikidata point)")
    mines.plot(ax=ax, color="#d73027", markersize=14, marker="^", zorder=4, label="Mining site")

    for _, row in pa_poly.iterrows():
        c = row.geometry.centroid
        ax.annotate(row["name"], (c.x, c.y), fontsize=7, ha="center", weight="bold",
                    xytext=(0, 6), textcoords="offset points")

    ax.set_title("Map 1 — Limpopo Regional Context\n"
                  "Province boundary, major protected areas, and mining locations",
                  fontsize=12, weight="bold")
    handles = [
        Patch(facecolor="#1a9850", edgecolor="#1a9850", alpha=0.35, label="Major protected area (real boundary, OSM)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#4575b4", markersize=7, label="Protected area (Wikidata point)"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#d73027", markersize=8, label="Mining site"),
        Line2D([0], [0], color="#9ecae1", linewidth=1.5, label="River (HydroRIVERS)"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7, framealpha=0.9)
    ax.text(0.99, 0.01, "CRS: ESRI:102022 (Africa Albers Equal Area Conic) | Sources: OSM, Wikidata, HydroRIVERS",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color="#555555")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_MAPS / "01_regional_context.png", dpi=150)
    plt.close(fig)
    print("  wrote 01_regional_context.png")


def map_02_mining_pressure():
    boundary = _load(config.BOUNDARY_GPKG, "limpopo_boundary")
    rivers = _load(config.RIVERS_GPKG, "rivers")
    pa = _load(config.PROTECTED_GPKG, "protected_areas")
    mines = _load(config.MINING_GPKG, "mining_sites")
    pinch = _load(config.CONNECTIVITY_GPKG, "mine_pinch_points")

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary, rivers)

    pa_poly = pa[pa["boundary_type"] == "polygon (OSM)"]
    pa_point = pa[pa["boundary_type"] != "polygon (OSM)"]
    pa_poly.plot(ax=ax, facecolor="#1a9850", edgecolor="#1a9850", alpha=0.3, linewidth=1.0, zorder=2)
    pa_point.plot(ax=ax, color="#a6d96a", markersize=8, zorder=2, alpha=0.8)
    mines.plot(ax=ax, color="#fdae61", markersize=14, marker="^", zorder=3, label="Mining site")
    pinch.plot(ax=ax, color="#7a0177", markersize=40, marker="^", zorder=4,
               edgecolor="black", linewidth=0.5, label=f"Mine within {10:.0f} km of a protected area (flagged)")

    ax.set_title("Map 2 — Mining Pressure and Protected Areas\n"
                  "Mining locations relative to protected areas and rivers",
                  fontsize=12, weight="bold")
    handles = [
        Patch(facecolor="#1a9850", edgecolor="#1a9850", alpha=0.3, label="Protected area"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#fdae61", markersize=8, label="Mining site"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#7a0177", markeredgecolor="black",
               markersize=10, label="Mine within 10 km of a protected area (Tier 3 hypothesis)"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7, framealpha=0.9)
    ax.text(0.99, 0.01, "10 km flag distance is a stated judgement call, not a species-specific "
                        "impact-zone threshold — see report §7",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color="#555555")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_MAPS / "02_mining_pressure.png", dpi=150)
    plt.close(fig)
    print("  wrote 02_mining_pressure.png")


def map_03_connectivity_opportunities():
    boundary = _load(config.BOUNDARY_GPKG, "limpopo_boundary")
    pa = _load(config.PROTECTED_GPKG, "protected_areas")
    documented = _load(config.CONNECTIVITY_GPKG, "documented_tfca_context")
    linkages = _load(config.CONNECTIVITY_GPKG, "candidate_linkages")

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary)

    pa_poly = pa[pa["boundary_type"] == "polygon (OSM)"]
    pa_point = pa[pa["boundary_type"] != "polygon (OSM)"]
    pa_poly.plot(ax=ax, facecolor="#cccccc", edgecolor="#888888", alpha=0.5, linewidth=0.8, zorder=1)
    pa_point.plot(ax=ax, color="#888888", markersize=6, zorder=1, alpha=0.6)

    linkages.plot(ax=ax, color="#fdae61", linewidth=0.5, linestyle="--", zorder=2,
                  label="Tier 2: inferred candidate linkage (NOT a designated corridor)")
    documented.plot(ax=ax, facecolor="#1a9850", edgecolor="#1a9850", alpha=0.45, linewidth=2.0, zorder=3,
                     label="Tier 1: documented TFCA context (GLTFCA / GMTFCA)")

    ax.set_title("Map 3 — Eco-connectivity Opportunities\n"
                  "Documented transfrontier context vs. inferred candidate linkages",
                  fontsize=12, weight="bold")
    handles = [
        Patch(facecolor="#1a9850", edgecolor="#1a9850", alpha=0.45,
              label="Tier 1: DOCUMENTED (GLTFCA/GMTFCA — cited mechanism)"),
        Line2D([0], [0], color="#fdae61", linewidth=1.5, linestyle="--",
               label="Tier 2: INFERRED candidate linkage (this study's spatial reasoning only)"),
        Patch(facecolor="#cccccc", edgecolor="#888888", alpha=0.5, label="Other protected area (not linked)"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7, framealpha=0.9)
    ax.text(0.99, 0.01, "Dashed orange lines are NOT designated corridors — centroid-to-centroid "
                        "distance <= 40 km, a stated threshold, not a validated dispersal distance",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color="#555555")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_MAPS / "03_connectivity_opportunities.png", dpi=150)
    plt.close(fig)
    print("  wrote 03_connectivity_opportunities.png")


def map_04_restoration_priorities():
    boundary = _load(config.BOUNDARY_GPKG, "limpopo_boundary")
    pa = _load(config.PROTECTED_GPKG, "protected_areas")
    documented = _load(config.CONNECTIVITY_GPKG, "documented_tfca_context")
    linkages = _load(config.CONNECTIVITY_GPKG, "candidate_linkages")
    pinch = _load(config.CONNECTIVITY_GPKG, "mine_pinch_points")

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary)

    pa_poly = pa[pa["boundary_type"] == "polygon (OSM)"]
    pa_poly.plot(ax=ax, facecolor="#cccccc", edgecolor="#888888", alpha=0.4, linewidth=0.8, zorder=1)
    linkages.plot(ax=ax, color="#fdae61", linewidth=0.4, linestyle="--", alpha=0.5, zorder=2)
    documented.plot(ax=ax, facecolor="#1a9850", edgecolor="#1a9850", alpha=0.3, linewidth=1.5, zorder=2)

    # Priority = Tier 3 pinch points within 5 km (tighter than the 10 km flag
    # distance) - a visually distinct "highest priority" sub-set, stated as
    # this study's own prioritisation rule, not an external standard.
    high_priority = pinch[pinch["distance_km"] <= 5.0]
    lower_priority = pinch[pinch["distance_km"] > 5.0]
    lower_priority.plot(ax=ax, color="#fee08b", markersize=30, marker="o", zorder=3,
                         edgecolor="black", linewidth=0.4, label="Restoration opportunity (5-10 km)")
    high_priority.plot(ax=ax, color="#d73027", markersize=55, marker="*", zorder=4,
                        edgecolor="black", linewidth=0.5, label="Priority restoration opportunity (<= 5 km)")

    for _, row in high_priority.iterrows():
        c = row.geometry
        ax.annotate(row["mine_name"], (c.x, c.y), fontsize=6, ha="left",
                    xytext=(5, 3), textcoords="offset points")

    ax.set_title("Map 4 — Mine Restoration and Connectivity Priorities\n"
                  "Mines closest to protected areas: where restoration could plausibly contribute "
                  "to landscape connectivity",
                  fontsize=11, weight="bold")
    handles = [
        Line2D([0], [0], marker="*", color="w", markerfacecolor="#d73027", markeredgecolor="black",
               markersize=14, label="Priority restoration opportunity (mine <= 5 km from a protected area)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#fee08b", markeredgecolor="black",
               markersize=9, label="Restoration opportunity (mine 5-10 km from a protected area)"),
        Patch(facecolor="#1a9850", edgecolor="#1a9850", alpha=0.3, label="Documented TFCA context"),
        Patch(facecolor="#cccccc", edgecolor="#888888", alpha=0.4, label="Other protected area"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7, framealpha=0.9)
    ax.text(0.99, 0.01, "Priority = spatial proximity only (this study's own threshold) — NOT a "
                        "substitute for site-level rehabilitation-liability or ecological assessment",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color="#555555")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_MAPS / "04_restoration_priorities.png", dpi=150)
    plt.close(fig)
    print("  wrote 04_restoration_priorities.png")
    print(f"  {len(high_priority)} priority (<=5km) + {len(lower_priority)} secondary (5-10km) "
          f"restoration opportunities identified")


def main():
    map_00_limpopo_at_a_glance()
    map_01_regional_context()
    map_02_mining_pressure()
    map_03_connectivity_opportunities()
    map_04_restoration_priorities()


if __name__ == "__main__":
    main()
