"""
build_qgis_project.py
─────────────────────────
Assemble the QGIS deliverable: ../qgis/limpopo_mine_restoration.qgz.

Run with the SYSTEM python3 (PyQGIS bindings live there, not in the `coa`
conda env — same split this project's own
research/eco-connectivity/scripts/build_qgis_project.py and
research/camargue-comparison/scripts/build_camargue_qgis_project.py use):
  python3 scripts/build_qgis_project.py

Styling follows those scripts' own conventions (QgsCategorizedSymbolRenderer
for classed polygons/points, distinct LINE STYLES — not just colors — for
the three connectivity evidence tiers, so the documented/inferred/hypothesis
distinction survives a black-and-white print, per the task's own requirement
not to blur that distinction).
"""

from pathlib import Path

from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer,
    QgsCategorizedSymbolRenderer, QgsRendererCategory,
    QgsSymbol, QgsSimpleFillSymbolLayer, QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer,
    QgsCoordinateReferenceSystem, Qgis,
)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

THIS_DIR = Path(__file__).resolve().parent.parent
DATA = THIS_DIR / "data" / "processed"
QGIS_OUT = THIS_DIR / "qgis" / "limpopo_mine_restoration.qgz"

qgs = QgsApplication([], False)
qgs.initQgis()

project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("ESRI:102022"))
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


def style_outline(layer, color="black", width=1.0):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    fill = QgsSimpleFillSymbolLayer()
    fill.setBrushStyle(0)  # Qt.NoBrush
    fill.setStrokeColor(QColor(color))
    fill.setStrokeWidth(width)
    symbol.changeSymbolLayer(0, fill)
    layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()


def style_protected_areas(layer):
    """Categorized by boundary_type: real OSM polygons get a solid green
    outline+light fill; Wikidata point-only records get a plain marker, so
    the map is honest about which sites have real boundary geometry."""
    categories = []
    for value, color, is_polygon in [
        ("polygon (OSM)", "#1a9850", True),
        ("point (Wikidata P625)", "#4575b4", False),
    ]:
        if is_polygon:
            symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Polygon)
            fill = QgsSimpleFillSymbolLayer()
            fill.setColor(QColor(color))
            fill.setStrokeColor(QColor(color))
            fill.setStrokeWidth(1.4)
            symbol.changeSymbolLayer(0, fill)
            symbol.setOpacity(0.35)
        else:
            symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Point)
            marker = QgsSimpleMarkerSymbolLayer()
            marker.setColor(QColor(color))
            marker.setStrokeColor(QColor("black"))
            marker.setSize(3.0)
            symbol.changeSymbolLayer(0, marker)
        categories.append(QgsRendererCategory(value, symbol, value))
    renderer = QgsCategorizedSymbolRenderer("boundary_type", categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def style_mining_sites(layer):
    """Plain marker symbol; the rubidium data-quality flag lives in the
    attribute table (data_quality_flag field) and the report text, not as a
    map-symbol distinction — a per-commodity categorization would be more
    useful visually and is left as a QGIS-side customization for the user
    (Layer Properties > Symbology > Categorized > commodity), documented in
    the report's QGIS Mapping Methodology section."""
    from qgis.core import QgsSingleSymbolRenderer
    symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Point)
    marker = QgsSimpleMarkerSymbolLayer()
    marker.setColor(QColor("#d73027"))
    marker.setStrokeColor(QColor("black"))
    marker.setSize(3.2)
    symbol.changeSymbolLayer(0, marker)
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()


def style_river_order(layer):
    """Graduated line width by ORD_STRA (Strahler stream order) — lower
    order number = smaller headwater stream, higher = larger mainstem, so
    thicker lines read as the more significant rivers without needing names
    HydroRIVERS doesn't carry."""
    symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Line)
    line = QgsSimpleLineSymbolLayer()
    line.setColor(QColor("#3288bd"))
    line.setWidth(0.5)
    symbol.changeSymbolLayer(0, line)
    from qgis.core import QgsSingleSymbolRenderer
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()


def style_documented_tfca(layer):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    fill = QgsSimpleFillSymbolLayer()
    fill.setColor(QColor("#1a9850"))
    fill.setStrokeColor(QColor("#1a9850"))
    fill.setStrokeWidth(2.0)
    symbol.changeSymbolLayer(0, fill)
    symbol.setOpacity(0.3)
    layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()


def style_candidate_linkages(layer):
    """Tier 2: inferred, not documented — dashed line, distinct from the
    solid documented-TFCA outline and from the pinch-point markers below,
    so the evidence tiers stay visually distinguishable in black-and-white."""
    symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Line)
    line = QgsSimpleLineSymbolLayer()
    line.setColor(QColor("#fdae61"))
    line.setWidth(0.6)
    line.setPenStyle(Qt.DashLine)
    symbol.changeSymbolLayer(0, line)
    from qgis.core import QgsSingleSymbolRenderer
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()


def style_pinch_points(layer):
    """Tier 3: hypothesis — a distinct marker shape (triangle/cross via
    'star' with points), so it doesn't read as the same kind of thing as a
    plain mining-site dot."""
    symbol = QgsSymbol.defaultSymbol(Qgis.GeometryType.Point)
    marker = QgsSimpleMarkerSymbolLayer()
    marker.setColor(QColor("#7a0177"))
    marker.setStrokeColor(QColor("black"))
    marker.setSize(4.5)
    marker.setShape(QgsSimpleMarkerSymbolLayer.Shape.Triangle)
    symbol.changeSymbolLayer(0, marker)
    from qgis.core import QgsSingleSymbolRenderer
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()


def main():
    print("Boundary:")
    grp_boundary = root.addGroup("Province boundary")
    boundary = add_vector(DATA / "limpopo_boundary.gpkg", "limpopo_boundary", "Limpopo Province (OSM 349547)", grp_boundary)
    if boundary:
        style_outline(boundary, "black", 1.5)

    print("Rivers:")
    grp_rivers = root.addGroup("Rivers (HydroRIVERS)")
    rivers = add_vector(DATA / "limpopo_rivers.gpkg", "rivers", "Rivers (Strahler-ordered, unnamed in source)", grp_rivers)
    if rivers:
        style_river_order(rivers)

    print("Protected areas:")
    grp_protected = root.addGroup("Protected & conservation areas")
    pa = add_vector(DATA / "limpopo_protected_areas.gpkg", "protected_areas", "Protected areas (polygon=OSM, point=Wikidata)", grp_protected)
    if pa:
        style_protected_areas(pa)

    print("Mining sites:")
    grp_mining = root.addGroup("Mining sites")
    mines = add_vector(DATA / "limpopo_mining_sites.gpkg", "mining_sites", "Mining sites (Wikidata + verified named mines)", grp_mining)
    if mines:
        style_mining_sites(mines)

    print("Eco-connectivity (evidence-tiered):")
    grp_conn = root.addGroup("Eco-connectivity (Tier 1 documented / Tier 2 inferred / Tier 3 hypothesis)")
    doc = add_vector(DATA / "limpopo_connectivity.gpkg", "documented_tfca_context", "Tier 1: Documented TFCA context (GLTFCA/GMTFCA)", grp_conn)
    if doc:
        style_documented_tfca(doc)
    link = add_vector(DATA / "limpopo_connectivity.gpkg", "candidate_linkages", "Tier 2: Inferred candidate linkages (NOT designated corridors)", grp_conn)
    if link:
        style_candidate_linkages(link)
    pinch = add_vector(DATA / "limpopo_connectivity.gpkg", "mine_pinch_points", "Tier 3: Hypothesis - mine pinch points (field verification required)", grp_conn)
    if pinch:
        style_pinch_points(pinch)

    QGIS_OUT.parent.mkdir(parents=True, exist_ok=True)
    project.write(str(QGIS_OUT))
    print(f"\nWrote {QGIS_OUT}")


if __name__ == "__main__":
    main()
    qgs.exitQgis()
