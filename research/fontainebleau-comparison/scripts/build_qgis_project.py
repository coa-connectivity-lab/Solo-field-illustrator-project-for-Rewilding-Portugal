"""
build_qgis_project.py
─────────────────────────
Assemble ../qgis/fontainebleau_ecotourism.qgz. Run with the SYSTEM python3
(PyQGIS bindings, not the `coa` conda env), same split as
research/camargue-comparison/scripts/build_camargue_qgis_project.py and
research/limpopo-mine-restoration/scripts/build_qgis_project.py.
"""

from pathlib import Path

from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer,
    QgsCategorizedSymbolRenderer, QgsRendererCategory,
    QgsSymbol, QgsSimpleFillSymbolLayer, QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer,
    QgsCoordinateReferenceSystem, Qgis, QgsSingleSymbolRenderer,
)
from qgis.PyQt.QtGui import QColor

THIS_DIR = Path(__file__).resolve().parent.parent
DATA = THIS_DIR / "data" / "processed"
QGIS_OUT = THIS_DIR / "qgis" / "fontainebleau_ecotourism.qgz"

qgs = QgsApplication([], False)
qgs.initQgis()

project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:2154"))
root = project.layerTreeRoot()


def add_vector(gpkg: Path, layer_name: str, display_name: str, group) -> QgsVectorLayer | None:
    uri = f"{gpkg}|layername={layer_name}"
    layer = QgsVectorLayer(uri, display_name, "ogr")
    if not layer.isValid():
        print(f"  INVALID vector: {uri}")
        return None
    project.addMapLayer(layer, False)
    group.addLayer(layer)
    print(f"  vector: {display_name} ({layer.featureCount()} features)")
    return layer


def style_outline(layer, color="black", width=1.2):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    fill = QgsSimpleFillSymbolLayer()
    fill.setBrushStyle(0)
    fill.setStrokeColor(QColor(color))
    fill.setStrokeWidth(width)
    symbol.changeSymbolLayer(0, fill)
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()


def style_protected_areas(layer):
    categories = []
    colors = {
        "UNESCO Biosphere Reserve": "#762a83",
        "Regional Nature Park": "#1b7837",
        "State Forest (ONF)": "#5aae61",
        "Réserve Biologique Intégrale (strict reserve)": "#d73027",
        "Réserve Biologique Dirigée (managed reserve)": "#fdae61",
    }
    for value, color in colors.items():
        symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Polygon)
        fill = QgsSimpleFillSymbolLayer()
        fill.setColor(QColor(color))
        fill.setStrokeColor(QColor(color))
        fill.setStrokeWidth(1.0)
        symbol.changeSymbolLayer(0, fill)
        symbol.setOpacity(0.45)
        categories.append(QgsRendererCategory(value, symbol, value))
    renderer = QgsCategorizedSymbolRenderer("designation", categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def style_species(layer):
    categories = []
    colors = {
        "mammal": "#b35806", "bird": "#2166ac", "reptile (Squamata only - see module docstring)": "#1a9850",
        "amphibian": "#66c2a5", "insect": "#f46d43", "vascular plant": "#762a83",
    }
    for value, color in colors.items():
        symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Point)
        marker = QgsSimpleMarkerSymbolLayer()
        marker.setColor(QColor(color))
        marker.setStrokeColor(QColor("black"))
        marker.setSize(2.6)
        symbol.changeSymbolLayer(0, marker)
        categories.append(QgsRendererCategory(value, symbol, value))
    renderer = QgsCategorizedSymbolRenderer("group", categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def style_facilities(layer):
    categories = []
    colors = {
        "climbing_area": "#d73027",
        "trail_information_point": "#4575b4",
        "parking": "#666666",
    }
    for value, color in colors.items():
        symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Point)
        marker = QgsSimpleMarkerSymbolLayer()
        marker.setColor(QColor(color))
        marker.setStrokeColor(QColor(color))
        marker.setSize(2.2)
        symbol.setOpacity(0.55)
        symbol.changeSymbolLayer(0, marker)
        categories.append(QgsRendererCategory(value, symbol, value))
    renderer = QgsCategorizedSymbolRenderer("facility_type", categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def main():
    print("Boundary:")
    grp_boundary = root.addGroup("Forest boundary")
    boundary = add_vector(DATA / "fontainebleau_boundary.gpkg", "fontainebleau_boundary", "Forêt de Fontainebleau (OSM 3236785)", grp_boundary)
    if boundary:
        style_outline(boundary, "black", 1.4)

    print("Protected areas:")
    grp_protected = root.addGroup("Protected areas (biosphere reserve, regional park, Réserves Biologiques)")
    pa = add_vector(DATA / "fontainebleau_protected_areas.gpkg", "protected_areas", "Protected areas", grp_protected)
    if pa:
        style_protected_areas(pa)

    print("Species occurrences:")
    grp_species = root.addGroup("Species occurrences (GBIF)")
    sp = add_vector(DATA / "fontainebleau_species_occurrences.gpkg", "occurrences", "Species occurrences by taxonomic group", grp_species)
    if sp:
        style_species(sp)

    print("Ecotourism facilities:")
    grp_facilities = root.addGroup("Ecotourism access & facilities")
    fac = add_vector(DATA / "fontainebleau_ecotourism_facilities.gpkg", "facilities", "Climbing areas, trail info points, parking", grp_facilities)
    if fac:
        style_facilities(fac)

    print("Fire history:")
    grp_fire = root.addGroup("Fire history (MODIS MCD64A1.061, 2015-2025)")
    fire = add_vector(DATA / "fontainebleau_fire_history.gpkg", "fire_history", "MODIS-detected burns", grp_fire)
    if fire and fire.featureCount() > 0:
        style_outline(fire, "#a50026", 1.0)
    elif fire:
        print("  (0 features - no MODIS-detected burns in the study window, skipping styling)")

    QGIS_OUT.parent.mkdir(parents=True, exist_ok=True)
    project.write(str(QGIS_OUT))
    print(f"\nWrote {QGIS_OUT}")


if __name__ == "__main__":
    main()
    qgs.exitQgis()
