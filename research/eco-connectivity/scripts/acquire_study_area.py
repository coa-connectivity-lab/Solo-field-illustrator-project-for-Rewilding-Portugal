"""
acquire_study_area.py
──────────────────────
Build the Côa Valley study area (v2: catchment-extended). Writes:
  data/processed/study_area.gpkg   (layers: coa_river, coa_catchment_rivers, study_area)

v1 built a flat 30km buffer around the OSM-derived Côa river centerline only. v2 adds a
second component: the Côa's own tributary network, traced from the national HydroRIVERS
dataset (data-management/data/raw/colab/hydrorivers_100.gpkg — part of the HydroSHEDS
family), so headwater tributaries that run beyond the 30km mainstem band are captured
too. No HydroBASINS-style watershed polygon exists in either repo, so this traces river
*topology* (NEXT_DOWN) rather than delineating a true DEM-based watershed — see the
"Catchment tracing method" note below for exactly what that does and doesn't capture.

Rewilding Portugal's own Greater Côa Valley project area (318,000 ha, per the annual
review / Endangered Landscapes project page) has no boundary polygon anywhere in either
repo — only prose description ("between the Malcata mountains and the Douro Valley").
Decision (confirmed with Linda): keep the river-buffer study area and document the
comparison rather than fabricate a precise boundary from prose — see the printed
comparison at the end of main().

Catchment tracing method:
1. Snap the OSM Côa centerline onto HydroRIVERS reaches (intersects a small buffer,
   config.CATCHMENT_SNAP_BUFFER_M).
2. Pick the Côa's own mouth reach as the snapped reach with the highest UPLAND_SKM
   (upstream drainage area) *below* config.CATCHMENT_MAX_PLAUSIBLE_UPLAND_SKM — the
   snap buffer also touches the Douro mainstem right at the confluence (whose upstream
   area is ~80,000+ km2), so without this ceiling the "mouth" pick would jump onto the
   Douro instead of stopping at the Côa's own outlet (verified this session: the
   Côa's traced mouth reach comes out to UPLAND_SKM=2,512.6 km2, matching the Côa's
   published ~2,495 km2 drainage-basin area almost exactly).
3. Recursively trace upstream from that mouth reach via NEXT_DOWN (inverted into an
   upstream-neighbours map), collecting every reach that eventually drains through it.
   This only goes *backward* from the Côa's own mouth, so it does not cross into the
   Douro's other, unrelated tributaries.
4. Buffer the traced network (config.TRIBUTARY_BUFFER_KM) and union with the original
   mainstem buffer.

Verified this session: this grows the study area from 9,377 km2 to ~10,230 km2 (+9%) —
a real but modest extension, since hydrorivers_100.gpkg's generalised tributary network
doesn't run dramatically wider than the mainstem's own OSM-line bounds for this basin.
Stated plainly rather than oversold.
"""

import geopandas as gpd
from shapely.ops import unary_union

import config

OUT_GPKG = config.DATA_PROCESSED / "study_area.gpkg"


def load_coa_river() -> gpd.GeoDataFrame:
    river = gpd.read_file(config.COA_RIVER_GPKG)
    if river.crs is None:
        river = river.set_crs(config.CRS_DISPLAY)
    return river


def load_hydrorivers_regional() -> gpd.GeoDataFrame:
    return gpd.read_file(
        config.HYDRORIVERS_GPKG,
        layer=config.HYDRORIVERS_LAYER,
        bbox=config.HYDRORIVERS_REGIONAL_BBOX,
    )


def find_coa_mouth_reach(hydro: gpd.GeoDataFrame, coa_river: gpd.GeoDataFrame):
    coa_metric = coa_river.to_crs(config.CRS_METRIC)
    snap_buffer = coa_metric.union_all().buffer(config.CATCHMENT_SNAP_BUFFER_M)
    snap_buffer_wgs84 = gpd.GeoSeries([snap_buffer], crs=config.CRS_METRIC).to_crs(config.CRS_DISPLAY).iloc[0]

    candidates = hydro[hydro.intersects(snap_buffer_wgs84)]
    if candidates.empty:
        raise RuntimeError(
            "No HydroRIVERS reaches matched to the OSM Côa line within "
            f"{config.CATCHMENT_SNAP_BUFFER_M}m — check HYDRORIVERS_REGIONAL_BBOX covers "
            "the Côa, or widen CATCHMENT_SNAP_BUFFER_M."
        )

    plausible = candidates[candidates["UPLAND_SKM"] < config.CATCHMENT_MAX_PLAUSIBLE_UPLAND_SKM]
    if plausible.empty:
        raise RuntimeError(
            "All snapped reaches exceed CATCHMENT_MAX_PLAUSIBLE_UPLAND_SKM — the ceiling "
            "may be excluding the real Côa mouth reach; inspect `candidates` manually."
        )
    return plausible.loc[plausible["UPLAND_SKM"].idxmax()], candidates


def trace_upstream_network(hydro: gpd.GeoDataFrame, mouth_hyriv_id: int) -> gpd.GeoDataFrame:
    upstream_of = {}
    for rid, next_down in zip(hydro["HYRIV_ID"], hydro["NEXT_DOWN"]):
        upstream_of.setdefault(next_down, []).append(rid)

    visited: set[int] = set()
    queue = [int(mouth_hyriv_id)]
    while queue:
        current = queue.pop()
        if current in visited:
            continue
        visited.add(current)
        queue.extend(up for up in upstream_of.get(current, []) if up not in visited)

    return hydro[hydro["HYRIV_ID"].isin(visited)]


def main() -> None:
    river = load_coa_river()
    river_metric = river.to_crs(config.CRS_METRIC)
    mainstem_buffer_m = config.STUDY_AREA_BUFFER_KM * 1000
    mainstem_buffer = river_metric.union_all().buffer(mainstem_buffer_m)

    print("Tracing Côa catchment from HydroRIVERS...")
    hydro = load_hydrorivers_regional()
    print(f"  {len(hydro)} HydroRIVERS reaches in the regional bbox {config.HYDRORIVERS_REGIONAL_BBOX}")

    mouth, snapped_candidates = find_coa_mouth_reach(hydro, river)
    print(
        f"  Côa mouth reach: HYRIV_ID={mouth['HYRIV_ID']}, "
        f"UPLAND_SKM={mouth['UPLAND_SKM']:.1f} (published Côa basin area: ~2,495 km2), "
        f"{len(snapped_candidates)} reaches snapped to the OSM line total"
    )

    catchment_rivers = trace_upstream_network(hydro, mouth["HYRIV_ID"])
    print(f"  Traced catchment: {len(catchment_rivers)} reaches, {catchment_rivers['LENGTH_KM'].sum():.1f} km total")

    catchment_rivers_metric = catchment_rivers.to_crs(config.CRS_METRIC)
    tributary_buffer_m = config.TRIBUTARY_BUFFER_KM * 1000
    tributary_buffer = catchment_rivers_metric.union_all().buffer(tributary_buffer_m)

    final_geom = unary_union([mainstem_buffer, tributary_buffer])
    study_area_metric = gpd.GeoDataFrame(
        {"name": ["coa_valley_catchment_extended"]},
        geometry=[final_geom],
        crs=config.CRS_METRIC,
    )

    river.to_file(OUT_GPKG, layer="coa_river", driver="GPKG")
    catchment_rivers.to_file(OUT_GPKG, layer="coa_catchment_rivers", driver="GPKG")
    study_area_metric.to_file(OUT_GPKG, layer="study_area", driver="GPKG")

    bounds = study_area_metric.to_crs(config.CRS_DISPLAY).total_bounds
    old_area_km2 = mainstem_buffer.area / 1e6
    new_area_km2 = study_area_metric.geometry.area.sum() / 1e6
    rp_area_km2 = config.REWILDING_PORTUGAL_PROJECT_AREA_HA / 100.0

    print(f"\nStudy area (v2, catchment-extended):")
    print(f"  Mainstem-only buffer (v1 equivalent): {old_area_km2:,.0f} km2")
    print(f"  With traced tributary catchment:      {new_area_km2:,.0f} km2 ({(new_area_km2/old_area_km2 - 1)*100:+.1f}%)")
    print(f"  Rewilding Portugal's own Greater Côa Valley project area (prose figure, no boundary polygon exists): {rp_area_km2:,.0f} km2")
    print(f"  -> the river-buffer study area is {new_area_km2/rp_area_km2:.1f}x larger by area and spans a comparable north-south range;")
    print(f"     kept as-is rather than fabricating a precise 318,000ha boundary from prose (see module docstring).")
    print(f"Extent (EPSG:4326): {bounds}")
    print(f"Wrote {OUT_GPKG}")


if __name__ == "__main__":
    main()
