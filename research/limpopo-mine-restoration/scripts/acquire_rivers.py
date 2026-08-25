"""
acquire_rivers.py
────────────────────
Major named rivers within Limpopo Province — landscape-connectivity context
(§7 of the report), not a hydrological dataset in its own right.

Source: HydroRIVERS (part of the HydroSHEDS family), already staged locally
at data-management/data/raw/colab/hydrorivers_100.gpkg for the Côa Valley
pipeline's own catchment-tracing work
(research/eco-connectivity/scripts/acquire_study_area.py). Checked before
assuming: this file is a GLOBAL extract (confirmed via fiona bounds:
approx -180..180 lon, -55..84 lat, 2.6M features), not Europe/Iberia-only, so
it legitimately covers South Africa too — reused here rather than falling
back to OSM waterway tags, since a curated global river-network dataset is
more authoritative than OSM's inconsistently-tagged waterway=river ways for
this purpose. Always read with a bbox filter first, per this project's own
established convention (see research/eco-connectivity/config.py) — never
load 2.6M features unfiltered.

Writes: data/processed/limpopo_rivers.gpkg, layer "rivers"
"""

import geopandas as gpd

import config

HYDRORIVERS_GPKG = "/home/linda/Documents/myData/data-management/data/raw/colab/hydrorivers_100.gpkg"


def main() -> None:
    boundary = gpd.read_file(config.BOUNDARY_GPKG, layer="limpopo_boundary")
    minx, miny, maxx, maxy = boundary.total_bounds

    rivers = gpd.read_file(HYDRORIVERS_GPKG, bbox=(minx, miny, maxx, maxy))
    print(f"{len(rivers)} HydroRIVERS segments in the Limpopo bbox (pre-clip)")

    rivers = rivers.to_crs(config.CRS_DISPLAY) if rivers.crs != config.CRS_DISPLAY else rivers
    clipped = gpd.clip(rivers, boundary)
    print(f"{len(clipped)} segments after clipping to the real province polygon")

    name_col = next((c for c in ["RIV_ORD", "NAME", "river_name"] if c in clipped.columns), None)
    if "NAME" in clipped.columns:
        named = clipped[clipped["NAME"].notna() & (clipped["NAME"].astype(str).str.len() > 0)]
        print(f"{len(named)} named segments; sample names:",
              sorted(named["NAME"].astype(str).unique().tolist())[:20])
    else:
        print("No 'NAME' field in this HydroRIVERS extract — river order/discharge fields only "
              "(check columns before assuming names are unavailable):", list(clipped.columns))

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    clipped.to_file(config.RIVERS_GPKG, layer="rivers", driver="GPKG")
    print(f"Wrote {config.RIVERS_GPKG}")


if __name__ == "__main__":
    main()
