"""
build_species_qgis_project.py
──────────────────────────────
Assemble: references/ecological-information/qgis/rewilding_portugal_species_2025.qgz

Source: RW_01_AnnualReview2025_ENGLISH_FINALWEB.pdf (Rewilding Portugal's 2025 annual
review). That document has no per-species coordinates anywhere - only aggregate counts
on the "Portugal in numbers" page (223 vertebrate species, 110 fungi, 376 plants, 680
invertebrates "registered in the areas") plus a handful of flagship species named in the
narrative (beaver, Sorraia horse, Tauros, cinereous/Egyptian vulture, red deer). So this
project does NOT plot species occurrence points - it joins a species table (compiled by
hand from the PDF, see data/annual_review_2025_species.csv) to the Greater Côa Valley
study-area boundary already used in research/eco-connectivity/qgis/, as a presence list
on the project area rather than a distribution map. Confirmed with Linda before building
(the alternative was real GBIF occurrence points for only the species already covered by
research/eco-connectivity/data/processed/gbif_occurrences.gpkg).

Run with the SYSTEM python3 (PyQGIS bindings are installed there, not in the `coa` conda
env) - same convention as research/eco-connectivity/scripts/build_qgis_project.py:
  python3 scripts/build_species_qgis_project.py
"""

from pathlib import Path

from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer,
    QgsSymbol, QgsSimpleFillSymbolLayer,
    QgsLayerTreeGroup, QgsCoordinateReferenceSystem,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsMarkerSymbol,
)
from qgis.PyQt.QtGui import QColor

CATEGORY_COLORS = {
    "Bird": "#1b9e77", "Mammal": "#d95f02", "Reptile": "#7570b3",
    "Amphibian": "#e7298a", "Invertebrate": "#66a61e", "Flora": "#e6ab02",
}

REFS_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = REFS_DIR / "data"
QGIS_OUT = REFS_DIR / "qgis" / "rewilding_portugal_species_2025.qgz"

# Read-only reference to the eco-connectivity project's study area - not duplicated here.
ECO_PROCESSED_DIR = REFS_DIR.parent.parent / "research" / "eco-connectivity" / "data" / "processed"

qgs = QgsApplication([], False)
qgs.initQgis()

project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:3035"))
root = project.layerTreeRoot()


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


def add_csv_table(path: Path, display_name: str, group):
    uri = f"file:///{path}?type=csv&detectTypes=yes&geomType=none"
    layer = QgsVectorLayer(uri, display_name, "delimitedtext")
    if not layer.isValid():
        print(f"  INVALID table: {uri}")
        return None
    project.addMapLayer(layer, False)
    group.addLayer(layer)
    print(f"  table: {display_name}")
    return layer


def add_csv_points(path: Path, x_field: str, y_field: str, display_name: str, group, crs: str = "EPSG:4326"):
    uri = f"file:///{path}?type=csv&detectTypes=yes&xField={x_field}&yField={y_field}&crs={crs}"
    layer = QgsVectorLayer(uri, display_name, "delimitedtext")
    if not layer.isValid():
        print(f"  INVALID points: {uri}")
        return None
    project.addMapLayer(layer, False)
    group.addLayer(layer)
    print(f"  points: {display_name}")
    return layer


def style_categorized(layer, field, colors, outline="black", outline_width=0.2, size=2.6):
    categories = []
    for value, color in colors.items():
        symbol = QgsMarkerSymbol.createSimple({
            "name": "circle", "color": color,
            "outline_color": outline, "outline_width": str(outline_width),
            "size": str(size),
        })
        categories.append(QgsRendererCategory(value, symbol, value))
    layer.setRenderer(QgsCategorizedSymbolRenderer(field, categories))
    layer.triggerRepaint()


def style_outline(layer, color="black", width=1.0):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    fill = QgsSimpleFillSymbolLayer()
    fill.setBrushStyle(0)  # Qt.NoBrush
    fill.setStrokeColor(QColor(color))
    fill.setStrokeWidth(width)
    symbol.changeSymbolLayer(0, fill)
    layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()


def main():
    print("Base context (Greater Côa Valley study area, read-only reference):")
    grp_base = root.addGroup("Base context")
    area = add_vector(ECO_PROCESSED_DIR / "study_area.gpkg", "study_area", "Greater Côa Valley study area (30km)", grp_base)
    if area:
        style_outline(area, "black", 1.2)
    river = add_vector(ECO_PROCESSED_DIR / "study_area.gpkg", "coa_river", "Côa river", grp_base)
    if river:
        style_outline(river, "#2166ac", 1.2)

    print("Species from RW_01_AnnualReview2025 (no coordinates in source - table only):")
    grp_species = root.addGroup("Rewilding Portugal 2025 Annual Review - species")
    add_csv_table(DATA_DIR / "annual_review_2025_species.csv", "Named species present (Greater Côa Valley)", grp_species)
    add_csv_table(DATA_DIR / "annual_review_2025_aggregate_counts.csv", "Aggregate species counts (not itemised in report)", grp_species)

    print("Visitor board / field-trip species (photographed panels, tourism sites, colleague-confirmed):")
    grp_visitor = root.addGroup("Visitor board species (field trips, Aug 2026)")
    visitor_layer = add_csv_points(
        DATA_DIR / "visitor_board_species_2026.csv", "x", "y",
        "Species — Faia Brava, Vale Carapito, Ermo das Águias, Ribeira do Mosteiro",
        grp_visitor,
    )
    if visitor_layer:
        style_categorized(visitor_layer, "map_category", CATEGORY_COLORS)

    QGIS_OUT.parent.mkdir(parents=True, exist_ok=True)
    project.write(str(QGIS_OUT))
    print(f"\nWrote {QGIS_OUT}")


if __name__ == "__main__":
    main()
    qgs.exitQgis()
