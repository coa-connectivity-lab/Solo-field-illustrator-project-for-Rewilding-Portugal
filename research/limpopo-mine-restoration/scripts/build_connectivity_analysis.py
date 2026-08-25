"""
build_connectivity_analysis.py
──────────────────────────────────
Evidence-tiered eco-connectivity analysis for Limpopo Province. This is a
regional-assessment-level analysis (distances, nearest-neighbour linkages,
documented-mechanism overlay), NOT a resistance-surface/least-cost-path
model like the Côa Valley's own research/eco-connectivity/ pipeline (which
uses Omniscape circuit-theory modelling over calibrated suitability rasters
for named focal species) — that would require land-cover, DEM, and road-
network rasters this study doesn't build. Said explicitly here and in the
report's Limitations section, not implied by omission.

Three tiers, carried through to the QGIS layers and the report prose:
  1. documented   — cites an actual named mechanism/source (GLTFCA, GMTFCA)
  2. inferred      — this script's own nearest-neighbour distance reasoning
  3. hypothesis    — a specific mine flagged as a potential pinch point,
                      requiring field verification, not asserted as fact

Writes: data/processed/limpopo_connectivity.gpkg
  layers: documented_tfca_context, candidate_linkages, mine_pinch_points
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

import config

# Distance threshold for an "inferred candidate linkage" between two protected
# areas: chosen as a round, clearly-stated cutoff, not derived from any
# species-specific home-range/dispersal-distance literature (that would need
# a named focal species and isn't attempted here) — 40 km is stated as a
# judgement call, not a scientific threshold, exactly as the report must be
# honest about.
LINKAGE_THRESHOLD_KM = 40.0

# Mine-to-linkage / mine-to-protected-area "pinch point" flag distance.
PINCH_THRESHOLD_KM = 10.0

# Protected areas already part of a documented transfrontier mechanism
# (GLTFCA or GMTFCA) - excluded from the "inferred" tier per the report's own
# evidence-tier rule (don't re-derive what's already documented).
DOCUMENTED_TFCA_MEMBERS = {
    "Kruger National Park": "GLTFCA (Great Limpopo Transfrontier Park) - internal veterinary "
        "fences with Limpopo NP (Mozambique) and Gonarezhou (Zimbabwe) removed since 2003. "
        "Figures per safari-upscaling-coa-valley-limpopo.md: ~10M ha GLTFCA, 3.7M ha fenced-core.",
    "Greater Kruger National Park": "Part of the broader Kruger-adjacent private-reserve network "
        "feeding into GLTFCA (see Kruger National Park entry).",
    "Mapungubwe National Park": "GMTFCA (Greater Mapungubwe Transfrontier Conservation Area) - "
        "fence-removal network with Northern Tuli Game Reserve (Botswana) and Tuli Circle Safari "
        "Area (Zimbabwe). Area figures disagree across sources checked: 4,872 km² (TFCA Portal) "
        "vs. 5,909 km² (Peace Parks Foundation) - both stated, not reconciled.",
}


def main() -> None:
    pa = gpd.read_file(config.PROTECTED_GPKG, layer="protected_areas").to_crs(config.CRS_METRIC)
    mines = gpd.read_file(config.MINING_GPKG, layer="mining_sites").to_crs(config.CRS_METRIC)

    # --- Tier 1: documented TFCA context (labelled, not computed) ---
    documented = pa[pa["name"].isin(DOCUMENTED_TFCA_MEMBERS)].copy()
    documented["tfca_note"] = documented["name"].map(DOCUMENTED_TFCA_MEMBERS)
    documented["evidence_tier"] = "1_documented"
    print(f"Tier 1 (documented TFCA context): {len(documented)} protected areas — "
          f"{sorted(documented['name'].tolist())}")

    # --- Tier 2: inferred candidate linkages between non-TFCA protected areas ---
    # Use centroids for a defensible, explainable nearest-neighbour distance
    # (not the polygon boundary-to-boundary distance for the point-only records,
    # which don't have a meaningful edge) - stated plainly as a simplification.
    pa["centroid"] = pa.geometry.centroid
    candidates = pa[~pa["name"].isin(DOCUMENTED_TFCA_MEMBERS)].copy()

    links = []
    names = candidates["name"].tolist()
    centroids = candidates.set_index("name")["centroid"]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            dist_km = centroids[a].distance(centroids[b]) / 1000
            if dist_km <= LINKAGE_THRESHOLD_KM:
                links.append({
                    "site_a": a, "site_b": b, "distance_km": round(dist_km, 1),
                    "geometry": LineString([centroids[a], centroids[b]]),
                    "evidence_tier": "2_inferred",
                    "note": f"Centroid-to-centroid distance {dist_km:.1f} km, below the "
                            f"{LINKAGE_THRESHOLD_KM:.0f} km judgement-call threshold used in this "
                            f"study - NOT a designated or documented corridor, and not validated "
                            f"against any species-specific dispersal distance.",
                })
    linkages = gpd.GeoDataFrame(links, geometry="geometry", crs=config.CRS_METRIC) if links else \
        gpd.GeoDataFrame(columns=["site_a", "site_b", "distance_km", "geometry", "evidence_tier", "note"],
                          geometry="geometry", crs=config.CRS_METRIC)
    print(f"Tier 2 (inferred candidate linkages, <= {LINKAGE_THRESHOLD_KM:.0f} km centroid distance): "
          f"{len(linkages)} pairs")

    # --- Tier 3: mine pinch points near an inferred linkage or a documented TFCA boundary ---
    pinch = []
    all_pa_for_pinch = pd.concat([documented[["name", "geometry"]], candidates[["name", "geometry"]]])
    for _, mine in mines.iterrows():
        nearest_dist_km = (all_pa_for_pinch.geometry.distance(mine.geometry) / 1000).min()
        if nearest_dist_km <= PINCH_THRESHOLD_KM:
            nearest_name = all_pa_for_pinch.loc[
                (all_pa_for_pinch.geometry.distance(mine.geometry) / 1000).idxmin(), "name"
            ]
            pinch.append({
                "mine_name": mine["name"],
                "commodity": mine["commodity"],
                "nearest_protected_area": nearest_name,
                "distance_km": round(nearest_dist_km, 1),
                "geometry": mine.geometry,
                "evidence_tier": "3_hypothesis",
                "note": f"{mine['name']} lies {nearest_dist_km:.1f} km from {nearest_name}'s "
                        f"boundary/centroid - flagged as a POTENTIAL pinch point requiring field "
                        f"verification, not an established finding. Proximity alone does not "
                        f"establish an ecological effect.",
            })
    pinch_gdf = gpd.GeoDataFrame(pinch, geometry="geometry", crs=config.CRS_METRIC) if pinch else \
        gpd.GeoDataFrame(columns=["mine_name", "commodity", "nearest_protected_area", "distance_km",
                                   "geometry", "evidence_tier", "note"], geometry="geometry", crs=config.CRS_METRIC)
    print(f"Tier 3 (hypothesis: mines within {PINCH_THRESHOLD_KM:.0f} km of a protected area): "
          f"{len(pinch_gdf)} flagged")

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    documented[["name", "designation", "tfca_note", "evidence_tier", "geometry"]].to_file(
        config.CONNECTIVITY_GPKG, layer="documented_tfca_context", driver="GPKG")
    linkages.to_file(config.CONNECTIVITY_GPKG, layer="candidate_linkages", driver="GPKG")
    pinch_gdf.to_file(config.CONNECTIVITY_GPKG, layer="mine_pinch_points", driver="GPKG")
    print(f"\nWrote {config.CONNECTIVITY_GPKG} (layers: documented_tfca_context, "
          f"candidate_linkages, mine_pinch_points)")

    if len(pinch_gdf):
        print("\nPinch points detail:")
        print(pinch_gdf[["mine_name", "commodity", "nearest_protected_area", "distance_km"]]
              .sort_values("distance_km").to_string(index=False))


if __name__ == "__main__":
    main()
