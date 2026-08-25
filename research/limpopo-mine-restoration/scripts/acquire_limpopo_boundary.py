"""
acquire_limpopo_boundary.py
──────────────────────────────
Limpopo province boundary — the clip mask every other layer in this study is
filtered against. Without this, a bounding-box discovery pull also catches
real North West Province platinum-belt mines (Bafokeng, Crocodile River,
Eland, near Rustenburg) and Mpumalanga's Sabi Sands Game Reserve — confirmed
during planning research, not a hypothetical risk.

Source: OSM relation 349547 (boundary=administrative), confirmed via direct
Nominatim query on 2026-08-25 ("Limpopo, South Africa" -> relation 349547).

Writes: data/processed/limpopo_boundary.gpkg, layer "limpopo_boundary"
"""

import geopandas as gpd
import osmnx as ox

import config


def main() -> None:
    gdf = ox.geocode_to_gdf(config.LIMPOPO_OSM_RELATION, by_osmid=True)
    gdf = gdf[["geometry"]].copy()
    gdf["name"] = "Limpopo Province"
    gdf["source"] = "OpenStreetMap relation 349547 (boundary=administrative)"
    gdf = gdf.set_crs(config.CRS_DISPLAY) if gdf.crs is None else gdf.to_crs(config.CRS_DISPLAY)

    area_ha = gdf.to_crs(config.CRS_METRIC).geometry.area.sum() / 10_000
    print(f"Limpopo boundary: {area_ha:,.0f} ha ({area_ha / 100:,.0f} km²) per OSM relation 349547")
    print("Published reference figure: 125,755 km² (10.4% of South Africa's national area; "
          "confirmed via web search 2026-08-25) — compare after running, don't assume a match")

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    gdf.to_file(config.BOUNDARY_GPKG, layer="limpopo_boundary", driver="GPKG")
    print(f"Wrote {config.BOUNDARY_GPKG}")


if __name__ == "__main__":
    main()
