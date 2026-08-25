"""
generate_maps.py
─────────────────────
Report-embedded PNG maps for the Camargue ecotourism comparison, output/maps/
— matplotlib/geopandas, same convention as research/fontainebleau-comparison/
scripts/generate_maps.py and research/limpopo-mine-restoration/scripts/
generate_maps.py: a `_base()` boundary helper, one function per map, a
source-credit footer text on every figure.

No config.py exists for this project (see acquire_camargue_layers.py) — paths
and CRS constants are inlined here to match that script's own convention.

All maps in CRS_METRIC (EPSG:3035, ETRS89-LAEA Europe).
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

CRS_METRIC = "EPSG:3035"

THIS_DIR = Path(__file__).resolve().parent.parent
GPKG = THIS_DIR / "data" / "processed" / "camargue_layers.gpkg"
OUTPUT_MAPS = THIS_DIR / "output" / "maps"
OUTPUT_MAPS.mkdir(parents=True, exist_ok=True)

DESIGNATION_COLORS = {
    "Regional Nature Park": "#1a9850",
    "National Nature Reserve (SNPN-managed)": "#4575b4",
}
HABITAT_COLORS = {
    "wetland": "#66c2a5", "water": "#3288bd", "salt_pond": "#f46d43",
    "beach": "#fee08b", "sand": "#fdae61", "scrub": "#a6d96a",
    "grassland": "#d9ef8b", "meadow": "#abdda4", "farmland": "#e6f598",
    "vineyard": "#c2a5cf",
}
FACILITY_COLORS = {
    "visitor_information": "#4575b4", "visitor_center": "#1a9850",
    "tour_operator_departure": "#d73027", "gateway_town": "#fdae61",
    "landmark_context": "#999999", "agritourism_site": "#762a83",
}
FACILITY_LABELS = {
    "visitor_information": "Visitor information", "visitor_center": "Visitor centre",
    "tour_operator_departure": "Tour/safari departure point", "gateway_town": "Gateway town",
    "landmark_context": "Landmark (orientation only)", "agritourism_site": "Agritourism site",
}

SOURCE_CREDIT = "CRS: EPSG:3035 (ETRS89-LAEA Europe) | Sources: OSM (Overpass/Nominatim)"


def _load(layer):
    return gpd.read_file(GPKG, layer=layer).to_crs(CRS_METRIC)


def _park_boundary(protected):
    return protected[protected["designation"] == "Regional Nature Park"]


def _base(ax, boundary):
    boundary.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=1.3, zorder=1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def _footer(ax, text=SOURCE_CREDIT):
    ax.text(0.99, 0.01, text, transform=ax.transAxes, fontsize=6,
             ha="right", va="bottom", color="#555555")


def map_00_camargue_at_a_glance():
    """Single combined figure distilling the core finding for a non-GIS
    reader: a large protected wetland core, reached from tourism gateways
    that mostly sit just outside it — checked spatially against the actual
    facility points rather than assumed (3 of 6 facilities fall inside the
    park boundary; the other 3 — Avignon, Arles, Bellegarde — are real
    gateway/departure points outside it, per acquire_camargue_layers.py)."""
    protected = _load("protected_areas")
    eco = _load("ecological_zones")
    facilities = _load("ecotourism_facilities")
    boundary = _park_boundary(protected)
    park_geom = boundary.geometry.iloc[0]
    n_inside = int(facilities.geometry.within(park_geom).sum())

    fig, ax = plt.subplots(figsize=(11, 10))
    _base(ax, boundary)

    for designation, color in DESIGNATION_COLORS.items():
        subset = protected[protected["designation"] == designation]
        if not subset.empty:
            alpha = 0.12 if designation == "Regional Nature Park" else 0.5
            subset.plot(ax=ax, facecolor=color, edgecolor=color, alpha=alpha, linewidth=1.2, zorder=2)

    wetland = eco[eco["habitat_type"].isin(["wetland", "water", "salt_pond"])]
    wetland.plot(ax=ax, facecolor="#3288bd", edgecolor="none", alpha=0.35, zorder=1.5)

    for ftype, color in FACILITY_COLORS.items():
        subset = facilities[facilities["facility_type"] == ftype]
        if not subset.empty:
            subset.plot(ax=ax, color=color, markersize=45, edgecolor="black", linewidth=0.5, zorder=4)

    ax.set_title(
        "Camargue at a glance\n"
        f"Protected wetland core ({n_inside} of {len(facilities)} tourism\n"
        "access points inside it, the rest are nearby gateways)",
        fontsize=13, weight="bold", loc="left")
    ax.text(
        0.01, 0.01,
        "Key implication: the strict reserve core is reached mainly via\n"
        "gateway towns and departure points just outside the park —\n"
        "access infrastructure and habitat core are spatially distinct.",
        transform=ax.transAxes, fontsize=8, ha="left", va="bottom",
        style="italic", color="#333333",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="#cccccc"))
    handles = [
        Patch(facecolor=DESIGNATION_COLORS["Regional Nature Park"], alpha=0.3, label="Regional Nature Park"),
        Patch(facecolor=DESIGNATION_COLORS["National Nature Reserve (SNPN-managed)"], alpha=0.5, label="National Nature Reserve (strict)"),
        Patch(facecolor="#3288bd", alpha=0.35, label="Wetland / water / salt pond"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#d73027", markersize=8, label="Tourism access point"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=7.5, framealpha=0.9)
    _footer(ax)
    fig.tight_layout()
    fig.savefig(OUTPUT_MAPS / "00_camargue_at_a_glance.png", dpi=150)
    plt.close(fig)
    print(f"  wrote 00_camargue_at_a_glance.png ({n_inside}/{len(facilities)} facilities inside park boundary)")


def map_01_protected_areas():
    protected = _load("protected_areas")
    boundary = _park_boundary(protected)

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary)

    for designation, color in DESIGNATION_COLORS.items():
        subset = protected[protected["designation"] == designation]
        if not subset.empty:
            alpha = 0.15 if designation == "Regional Nature Park" else 0.6
            subset.plot(ax=ax, facecolor=color, edgecolor=color, alpha=alpha, linewidth=1.4, zorder=2)

    ax.set_title("Map 1 — Camargue protected-area context\n"
                  "Regional Nature Park boundary and the SNPN-managed National Nature Reserve within it",
                  fontsize=12, weight="bold")
    handles = [Patch(facecolor=c, edgecolor=c, alpha=(0.3 if d == "Regional Nature Park" else 0.7), label=d)
               for d, c in DESIGNATION_COLORS.items()]
    ax.legend(handles=handles, loc="lower left", fontsize=7, framealpha=0.9)
    _footer(ax)
    fig.tight_layout()
    fig.savefig(OUTPUT_MAPS / "01_protected_areas.png", dpi=150)
    plt.close(fig)
    print("  wrote 01_protected_areas.png")


def map_02_ecological_zones():
    protected = _load("protected_areas")
    eco = _load("ecological_zones")
    boundary = _park_boundary(protected)

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary)

    for habitat, color in HABITAT_COLORS.items():
        subset = eco[eco["habitat_type"] == habitat]
        if not subset.empty:
            subset.plot(ax=ax, facecolor=color, edgecolor="none", alpha=0.75, zorder=2)

    ax.set_title(f"Map 2 — Ecological zones by OSM habitat tag (n={len(eco)})\n"
                  "Coarse tag-derived proxy, not a calibrated land-cover classification",
                  fontsize=12, weight="bold")
    present = [h for h in HABITAT_COLORS if not eco[eco["habitat_type"] == h].empty]
    handles = [Patch(facecolor=HABITAT_COLORS[h], alpha=0.75, label=h) for h in present]
    ax.legend(handles=handles, loc="lower left", fontsize=6.5, framealpha=0.9, ncol=2)
    _footer(ax, SOURCE_CREDIT + " (natural=*/landuse=* tags — see acquisition script docstring caveat)")
    fig.tight_layout()
    fig.savefig(OUTPUT_MAPS / "02_ecological_zones.png", dpi=150)
    plt.close(fig)
    print("  wrote 02_ecological_zones.png")


def map_03_ecotourism_facilities():
    protected = _load("protected_areas")
    facilities = _load("ecotourism_facilities")
    boundary = _park_boundary(protected)
    reserve = protected[protected["designation"] == "National Nature Reserve (SNPN-managed)"]

    fig, ax = plt.subplots(figsize=(10, 9))
    _base(ax, boundary)
    reserve.plot(ax=ax, facecolor="#4575b4", edgecolor="#4575b4", alpha=0.2, linewidth=0.8, zorder=1)

    for ftype, color in FACILITY_COLORS.items():
        subset = facilities[facilities["facility_type"] == ftype]
        if not subset.empty:
            subset.plot(ax=ax, color=color, markersize=50, edgecolor="black", linewidth=0.5,
                        zorder=3, label=FACILITY_LABELS[ftype])

    ax.set_title(f"Map 3 — Ecotourism access & facilities (n={len(facilities)})\n"
                  "Blue tint: SNPN-managed National Nature Reserve (strict)",
                  fontsize=12, weight="bold")
    present = [f for f in FACILITY_COLORS if not facilities[facilities["facility_type"] == f].empty]
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=FACILITY_COLORS[f],
                       markersize=7, label=FACILITY_LABELS[f]) for f in present]
    ax.legend(handles=handles, loc="lower left", fontsize=7, framealpha=0.9)
    _footer(ax, SOURCE_CREDIT + " + itinerary geocoding")
    fig.tight_layout()
    fig.savefig(OUTPUT_MAPS / "03_ecotourism_facilities.png", dpi=150)
    plt.close(fig)
    print("  wrote 03_ecotourism_facilities.png")


def main():
    map_00_camargue_at_a_glance()
    map_01_protected_areas()
    map_02_ecological_zones()
    map_03_ecotourism_facilities()


if __name__ == "__main__":
    main()
