"""
build_qgis_project.py
─────────────────────────
Assemble the QGIS deliverable: research/eco-connectivity/qgis/coa_eco_connectivity_ecotourism.qgz

Run with the SYSTEM python3 (PyQGIS bindings are installed there, not in the
`coa` conda env):  python3 scripts/build_qgis_project.py

Styling follows data-management/docs/07_qgis_analysis_protocol.md: singleband
pseudocolor, RdYlBu reversed, for the normalised-current connectivity layers;
data-management/qgis/coa_connectivity.qgz is the starting template this
project's layer-group structure follows.
"""

import sys
from pathlib import Path

from qgis.core import (
    QgsApplication, QgsProject, QgsRasterLayer, QgsVectorLayer,
    QgsRasterShader, QgsColorRampShader, QgsSingleBandPseudoColorRenderer,
    QgsStyle, QgsCategorizedSymbolRenderer, QgsRendererCategory,
    QgsSymbol, QgsSimpleFillSymbolLayer, QgsSimpleMarkerSymbolLayer,
    QgsLayerTreeGroup, QgsCoordinateReferenceSystem,
)
from qgis.PyQt.QtGui import QColor

ECO_DIR = Path(__file__).resolve().parent.parent
RASTER_DIR = ECO_DIR / "output" / "rasters"
PROCESSED_DIR = ECO_DIR / "data" / "processed"
COVARIATE_DIR = PROCESSED_DIR / "covariates"
RESISTANCE_DIR = PROCESSED_DIR / "resistance"
QGIS_OUT = ECO_DIR / "qgis" / "coa_eco_connectivity_ecotourism.qgz"

qgs = QgsApplication([], False)
qgs.initQgis()

project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:3035"))
root = project.layerTreeRoot()


def style_connectivity_raster(layer: QgsRasterLayer, reversed_ramp=True):
    provider = layer.dataProvider()
    stats = provider.bandStatistics(1)
    vmin, vmax = stats.minimumValue, stats.maximumValue
    ramp = QgsStyle.defaultStyle().colorRamp("RdYlBu")
    if reversed_ramp:
        ramp.invert()
    shader = QgsColorRampShader(vmin, vmax, ramp, QgsColorRampShader.Interpolated)
    shader.classifyColorRamp(5, -1)
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader)
    renderer = QgsSingleBandPseudoColorRenderer(provider, 1, raster_shader)
    layer.setRenderer(renderer)
    layer.setOpacity(0.85)


def add_raster(path: Path, name: str, group, style_connectivity=True):
    layer = QgsRasterLayer(str(path), name)
    if not layer.isValid():
        print(f"  INVALID raster: {path}")
        return None
    project.addMapLayer(layer, False)
    group.addLayer(layer)
    if style_connectivity:
        style_connectivity_raster(layer)
    print(f"  raster: {name}")
    return layer


def add_vector(path: Path, layer_name: str, display_name: str, group):
    uri = f"{path}|layername={layer_name}"
    layer = QgsVectorLayer(uri, display_name, "ogr")
    if not layer.isValid():
        print(f"  INVALID vector: {uri}")
        return None
    project.addMapLayer(layer, False)
    group.addLayer(layer)
    print(f"  vector: {display_name}")
    return layer


def style_outline(layer, color="black", width=0.8):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    fill = QgsSimpleFillSymbolLayer()
    fill.setBrushStyle(0)  # Qt.NoBrush
    fill.setStrokeColor(QColor(color))
    fill.setStrokeWidth(width)
    symbol.changeSymbolLayer(0, fill)
    layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()


def style_points(layer, color, size=3):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    marker = QgsSimpleMarkerSymbolLayer()
    marker.setColor(QColor(color))
    marker.setSize(size)
    symbol.changeSymbolLayer(0, marker)
    layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()


def style_fire_raster(layer):
    provider = layer.dataProvider()
    stats = provider.bandStatistics(1)
    ramp = QgsStyle.defaultStyle().colorRamp("YlOrRd")
    shader = QgsColorRampShader(stats.minimumValue, stats.maximumValue, ramp, QgsColorRampShader.Interpolated)
    shader.classifyColorRamp(6, -1)
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader)
    renderer = QgsSingleBandPseudoColorRenderer(provider, 1, raster_shader)
    layer.setRenderer(renderer)
    layer.setOpacity(0.85)


def style_hunting_zones(layer):
    categories = []
    colors = {"ZCM": "#fdae61", "ZCA": "#abd9e9", "ZCT": "#d7191c"}
    for value, color in colors.items():
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        fill = QgsSimpleFillSymbolLayer()
        fill.setColor(QColor(color))
        fill.setStrokeStyle(0)
        symbol.changeSymbolLayer(0, fill)
        symbol.setOpacity(0.4)
        categories.append(QgsRendererCategory(value, symbol, value))
    renderer = QgsCategorizedSymbolRenderer("fig_ord", categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def main():
    print("Connectivity rasters:")
    grp_connectivity = root.addGroup("Connectivity (land / water / air)")
    for name, label in [
        ("land_normalized_current", "Land connectivity (wolf/wildcat/red deer)"),
        ("water_normalized_current", "Water connectivity (otter/fish/pond turtle)"),
        ("air_normalized_current", "Air connectivity (vultures/golden eagle)"),
        ("multispecies_mean_connectivity", "Multispecies connectivity (weighted mean)"),
        ("multispecies_max_connectivity", "Multispecies connectivity (max)"),
    ]:
        add_raster(RASTER_DIR / f"{name}.tif", label, grp_connectivity)

    print("Trade-off maps:")
    grp_tradeoff = root.addGroup("Roads & waterways: barrier vs. access")
    for name, label in [
        ("road_tradeoff_class", "Road trade-off class"),
        ("waterway_tradeoff_class", "Waterway trade-off class"),
        ("road_barrier_severity", "Road barrier severity"),
        ("road_access_value", "Road eco-tourism access value"),
        ("waterway_barrier_severity", "Waterway barrier severity"),
        ("waterway_access_value", "Waterway eco-tourism access value"),
    ]:
        add_raster(RASTER_DIR / f"{name}.tif", label, grp_tradeoff)

    print("Fire history (barrier to land restoration, v2 addition):")
    grp_fire = root.addGroup("Fire history")
    fire = add_raster(COVARIATE_DIR / "fire_last_burn_year.tif", "Most recent burn year (MODIS MCD64A1, real data)", grp_fire, style_connectivity=False)
    if fire:
        style_fire_raster(fire)
    fire_effect = add_raster(RESISTANCE_DIR / "land_resistance_no_fire.tif", "Land resistance without fire penalty (diagnostic)", grp_fire, style_connectivity=False)
    if fire_effect:
        style_connectivity_raster(fire_effect, reversed_ramp=False)

    print("Base context:")
    grp_base = root.addGroup("Base context")
    river = add_vector(PROCESSED_DIR / "study_area.gpkg", "coa_river", "Côa river (OSM mainstem)", grp_base)
    if river:
        style_outline(river, "#2166ac", 1.2)
    tributaries = add_vector(PROCESSED_DIR / "study_area.gpkg", "coa_catchment_rivers", "Traced tributary network (HydroRIVERS)", grp_base)
    if tributaries:
        style_outline(tributaries, "#67a9cf", 0.5)
    area = add_vector(PROCESSED_DIR / "study_area.gpkg", "study_area", "Study area (30km buffer + traced catchment)", grp_base)
    if area:
        style_outline(area, "black", 1.0)
    natura = add_vector(PROCESSED_DIR / "hydrology_and_protected_areas.gpkg", "natura2000", "Natura 2000", grp_base)
    if natura:
        style_outline(natura, "#1a9850", 0.8)
    water = add_vector(PROCESSED_DIR / "hydrology_and_protected_areas.gpkg", "water_bodies", "Water bodies (APA/WISE)", grp_base)
    if water:
        style_outline(water, "#4393c3", 0.6)

    print("Land tenure:")
    grp_tenure = root.addGroup("Land tenure context")
    hunting = add_vector(PROCESSED_DIR / "land_tenure.gpkg", "hunting_zones", "ICNF hunting zones (ZCM/ZCA/ZCT)", grp_tenure)
    if hunting:
        style_hunting_zones(hunting)
    reserves = add_vector(PROCESSED_DIR / "land_tenure.gpkg", "private_reserves", "Private reserves (Faia Brava)", grp_tenure)
    if reserves:
        style_outline(reserves, "#1a9850", 2.0)

    print("Field sites & eco-tourism:")
    grp_sites = root.addGroup("Field sites & eco-tourism")
    visited = add_vector(PROCESSED_DIR / "field_observations.gpkg", "visited_sites", "Visited sites (Survey123)", grp_sites)
    if visited:
        style_points(visited, "#d73027", 3.5)
    not_visited = add_vector(PROCESSED_DIR / "tourism_sites.gpkg", "not_yet_visited", "Not yet visited", grp_sites)
    if not_visited:
        style_points(not_visited, "#4575b4", 3.5)
    ecotourism = add_vector(PROCESSED_DIR / "tourism_sites.gpkg", "potential_ecotourism_sites", "Potential eco-tourism sites", grp_sites)
    if ecotourism:
        style_points(ecotourism, "#fee08b", 4.0)

    QGIS_OUT.parent.mkdir(parents=True, exist_ok=True)
    project.write(str(QGIS_OUT))
    print(f"\nWrote {QGIS_OUT}")


if __name__ == "__main__":
    main()
    qgs.exitQgis()
