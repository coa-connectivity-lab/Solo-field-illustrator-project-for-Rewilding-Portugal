"""
build_camargue_qgis_project.py
─────────────────────────────────
Assemble the QGIS deliverable: ../qgis/camargue_ecotourism.qgz — ecological
zones, protected-area boundaries, and ecotourism access/facility points for
the Camargue, companion map to
field-trips/deskStudy/camargue-ecotourism-implications-coa-valley.md.

Run with the SYSTEM python3 (PyQGIS bindings live there, not in the `coa`
conda env — same split this project's own
research/eco-connectivity/scripts/build_qgis_project.py uses):
  python3 scripts/build_camargue_qgis_project.py

Styling follows that script's own conventions (QgsCategorizedSymbolRenderer
for classed polygons/points, plain outline symbols for boundaries) so this
map reads consistently with the rest of the project's QGIS deliverables.
"""

from pathlib import Path

from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer,
    QgsCategorizedSymbolRenderer, QgsRendererCategory,
    QgsSymbol, QgsSimpleFillSymbolLayer, QgsSimpleMarkerSymbolLayer,
    QgsCoordinateReferenceSystem,
)
from qgis.PyQt.QtGui import QColor

CAMARGUE_DIR = Path(__file__).resolve().parent.parent
GPKG = CAMARGUE_DIR / "data" / "processed" / "camargue_layers.gpkg"
QGIS_OUT = CAMARGUE_DIR / "qgis" / "camargue_ecotourism.qgz"

qgs = QgsApplication([], False)
qgs.initQgis()

project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:3035"))
root = project.layerTreeRoot()


def add_vector(layer_name: str, display_name: str, group) -> QgsVectorLayer | None:
    uri = f"{GPKG}|layername={layer_name}"
    layer = QgsVectorLayer(uri, display_name, "ogr")
    if not layer.isValid():
        print(f"  INVALID vector: {uri}")
        return None
    project.addMapLayer(layer, False)
    group.addLayer(layer)
    print(f"  vector: {display_name}")
    return layer


def style_outline(layer, color="black", width=1.2):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    fill = QgsSimpleFillSymbolLayer()
    fill.setBrushStyle(0)  # Qt.NoBrush
    fill.setStrokeColor(QColor(color))
    fill.setStrokeWidth(width)
    symbol.changeSymbolLayer(0, fill)
    layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()


def style_protected_areas(layer):
    """Categorized outline-only styling by designation, so the 82,000 ha
    regional park and the 13,232 ha national reserve inside it both read
    clearly rather than one obscuring the other."""
    categories = []
    colors = {
        "Regional Nature Park": "#1a9850",
        "National Nature Reserve (SNPN-managed)": "#4575b4",
    }
    for value, color in colors.items():
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        fill = QgsSimpleFillSymbolLayer()
        fill.setBrushStyle(0)
        fill.setStrokeColor(QColor(color))
        fill.setStrokeWidth(1.6 if "Reserve" in value else 1.0)
        symbol.changeSymbolLayer(0, fill)
        categories.append(QgsRendererCategory(value, symbol, value))
    renderer = QgsCategorizedSymbolRenderer("designation", categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def style_ecological_zones(layer):
    """Categorized fill by OSM-tag habitat_type — a coarse ecological-region
    proxy, not a calibrated land-cover classification (see acquisition
    script's docstring caveat)."""
    categories = []
    colors = {
        "wetland": "#66c2a5",
        "water": "#3288bd",
        "salt_pond": "#f46d43",
        "beach": "#fee08b",
        "sand": "#fdae61",
        "scrub": "#a6d96a",
        "grassland": "#d9ef8b",
        "meadow": "#abdda4",
        "farmland": "#e6f598",
        "vineyard": "#c2a5cf",
    }
    for value, color in colors.items():
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        fill = QgsSimpleFillSymbolLayer()
        fill.setColor(QColor(color))
        fill.setStrokeStyle(0)
        symbol.changeSymbolLayer(0, fill)
        symbol.setOpacity(0.75)
        categories.append(QgsRendererCategory(value, symbol, value))
    renderer = QgsCategorizedSymbolRenderer("habitat_type", categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def style_facilities(layer):
    """Categorized point markers by facility_type."""
    categories = []
    colors = {
        "visitor_information": "#4575b4",
        "visitor_center": "#1a9850",
        "tour_operator_departure": "#d73027",
        "gateway_town": "#fdae61",
        "landmark_context": "#999999",
        "agritourism_site": "#762a83",
    }
    for value, color in colors.items():
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        marker = QgsSimpleMarkerSymbolLayer()
        marker.setColor(QColor(color))
        marker.setStrokeColor(QColor("black"))
        marker.setSize(4.0)
        symbol.changeSymbolLayer(0, marker)
        categories.append(QgsRendererCategory(value, symbol, value))
    renderer = QgsCategorizedSymbolRenderer("facility_type", categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def main():
    print("Ecological zones:")
    grp_eco = root.addGroup("Ecological zones (OSM habitat tags — coarse proxy)")
    eco = add_vector("ecological_zones", "Habitat type", grp_eco)
    if eco:
        style_ecological_zones(eco)

    print("Protected areas:")
    grp_protected = root.addGroup("Protected areas")
    protected = add_vector("protected_areas", "Park / reserve boundaries", grp_protected)
    if protected:
        style_protected_areas(protected)

    print("Ecotourism access & facilities:")
    grp_facilities = root.addGroup("Ecotourism access & facilities")
    facilities = add_vector("ecotourism_facilities", "Access points & facilities", grp_facilities)
    if facilities:
        style_facilities(facilities)

    QGIS_OUT.parent.mkdir(parents=True, exist_ok=True)
    project.write(str(QGIS_OUT))
    print(f"\nWrote {QGIS_OUT}")


if __name__ == "__main__":
    main()
    qgs.exitQgis()
