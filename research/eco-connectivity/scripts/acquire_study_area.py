"""
acquire_study_area.py
──────────────────────
Build the Côa Valley study area: a 30km buffer around the Côa river
centerline (config.STUDY_AREA_BUFFER_KM), in both display (EPSG:4326)
and metric (EPSG:3035) CRS. Writes:
  data/processed/study_area.gpkg   (layers: coa_river, study_area)
"""

import geopandas as gpd

import config

OUT_GPKG = config.DATA_PROCESSED / "study_area.gpkg"


def main() -> None:
    river = gpd.read_file(config.COA_RIVER_GPKG)
    if river.crs is None:
        river = river.set_crs(config.CRS_DISPLAY)

    river_metric = river.to_crs(config.CRS_METRIC)
    buffer_m = config.STUDY_AREA_BUFFER_KM * 1000
    study_area_metric = gpd.GeoDataFrame(
        {"name": ["coa_valley_30km"]},
        geometry=[river_metric.union_all().buffer(buffer_m)],
        crs=config.CRS_METRIC,
    )

    river.to_file(OUT_GPKG, layer="coa_river", driver="GPKG")
    study_area_metric.to_file(OUT_GPKG, layer="study_area", driver="GPKG")

    bounds = study_area_metric.to_crs(config.CRS_DISPLAY).total_bounds
    print(f"Study area: {config.STUDY_AREA_BUFFER_KM}km buffer around {len(river)} Côa river segments")
    print(f"Extent (EPSG:4326): {bounds}")
    print(f"Area: {study_area_metric.geometry.area.sum() / 1e6:,.0f} km2")
    print(f"Wrote {OUT_GPKG}")


if __name__ == "__main__":
    main()
