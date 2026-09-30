"""Step 5: build the QGIS verification project and render check views over the
OpenStreetMap basemap.

Uses the system PyQGIS (not the conda env):
    python3 scripts/05_build_qgis_project.py
Writes output/coa_river_check.qgz (relative paths) and output/qgis_*.png
"""
import sys
import unicodedata
from pathlib import Path

from qgis.core import (QgsApplication, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsMapRendererParallelJob, QgsMapSettings, QgsPointXY, QgsProject,
                       QgsRasterLayer, QgsRectangle, QgsReferencedRectangle, QgsBookmark,
                       QgsVectorLayer)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "raw", ROOT / "output"
RASTERS = Path("/home/linda/Documents/myData/coa-eco-connectivity-data-v6/research/eco-connectivity/output/rasters")
MAPS = {"movement": "land_normalized_current.tif", "water": "water_normalized_current.tif",
        "connection": "multispecies_mean_connectivity.tif"}

qgs = QgsApplication([], False)
qgs.initQgis()
project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:3035"))
project.setFileName(str(OUT / "coa_river_check.qgz"))
root = project.layerTreeRoot()


def group(name):
    return root.addGroup(name)


def add(layer, grp, visible=True):
    if not layer.isValid():
        sys.exit(f"invalid layer: {layer.name()} {layer.source()}")
    project.addMapLayer(layer, False)
    node = grp.addLayer(layer)
    node.setItemVisibilityChecked(visible)
    return layer


def line_style(layer, color, width, dash=False):
    sym = layer.renderer().symbol()
    sym.setColor(QColor(color))
    sym.setWidth(width)
    if dash:
        from qgis.PyQt.QtCore import Qt
        sym.symbolLayer(0).setPenStyle(Qt.DashLine)


# Groups, top of legend first
g_check = group("Check layers")
g_png = group("Website map PNGs (georeferenced)")
g_src = group("Source rasters (v6 bundle)")
g_base = group("Basemap")

# Reference rivers and check layers
osm = add(QgsVectorLayer(str(RAW / "osm_coa_overpass.geojson"), "OSM Côa (Overpass, fresh)", "ogr"), g_check)
line_style(osm, "#00bcd4", 1.4)
bundle = add(QgsVectorLayer(f"{RAW / 'bundle_study_area.gpkg'}|layername=coa_river",
                            "bundle coa_river (drawn on website maps)", "ogr"), g_check)
line_style(bundle, "#10233f", 0.5)
hyd = add(QgsVectorLayer(str(OUT / "hydrorivers_main_stem.gpkg"), "HydroRIVERS Côa main stem", "ogr"), g_check)
line_style(hyd, "#e91e63", 0.5, dash=True)
douro = add(QgsVectorLayer(str(RAW / "osm_douro_overpass.geojson"), "OSM Douro (Overpass, fresh)", "ogr"), g_check)
line_style(douro, "#3f51b5", 1.0)
gaps = add(QgsVectorLayer(str(OUT / "gaps.gpkg"), "gaps in bundle line", "ogr"), g_check)
gaps.renderer().symbol().setColor(QColor("red"))
gaps.renderer().symbol().setSize(4)
sa = add(QgsVectorLayer(f"{RAW / 'bundle_study_area.gpkg'}|layername=study_area", "study area", "ogr"), g_check)
sa.renderer().symbol().symbolLayer(0).setFillColor(QColor(0, 0, 0, 0))
sa.renderer().symbol().symbolLayer(0).setStrokeColor(QColor("#555555"))
for name in MAPS:
    lyr = add(QgsVectorLayer(f"{OUT / 'image_line.gpkg'}|layername={name}",
                             f"line pixels extracted from map-{name}.png", "ogr"), g_check, visible=False)
    lyr.renderer().symbol().setColor(QColor("#ff9800"))
    lyr.renderer().symbol().setSize(0.6)

# Georeferenced PNGs (world files) and source rasters
for name in MAPS:
    png = add(QgsRasterLayer(str(RAW / f"map-{name}.png"), f"map-{name}.png"), g_png, visible=(name == "water"))
    png.setCrs(QgsCoordinateReferenceSystem("EPSG:3035"))
    png.renderer().setOpacity(0.6)
for name, tif in MAPS.items():
    add(QgsRasterLayer(str(RASTERS / tif), tif), g_src, visible=False)

osm_tiles = add(QgsRasterLayer(
    "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0",
    "OpenStreetMap", "wms"), g_base)

# Bookmarks at checkpoints along the river (lon, lat, half-width km)
to3035 = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"),
                                QgsCoordinateReferenceSystem("EPSG:3035"), project)
PLACES = {
    "Côa source (Serra da Malcata)": (-6.93, 40.28, 6),
    "Sabugal (gap 241 m)": (-7.0926, 40.3356, 3),
    "Gap 16 m": (-7.0187, 40.8027, 1),
    "Penascosa / Vila Nova de Foz Côa": (-7.10, 41.02, 8),
    "Côa-Douro confluence": (-7.12, 41.08, 3),
    "Whole study area": (-7.07, 40.66, 55),
}
bm = project.bookmarkManager()
for label, (lon, lat, km) in PLACES.items():
    p = to3035.transform(QgsPointXY(lon, lat))
    r = QgsRectangle(p.x() - km * 1000, p.y() - km * 1000 * 1.3, p.x() + km * 1000, p.y() + km * 1000 * 1.3)
    b = QgsBookmark()
    b.setName(label)
    b.setExtent(QgsReferencedRectangle(r, project.crs()))
    bm.addBookmark(b)

project.writeEntryBool("Paths", "/Absolute", False)
project.write()
print("wrote", project.fileName())


# Render check views over the OSM basemap
def render(fname, extent, layers, px=(900, 1300)):
    ms = QgsMapSettings()
    ms.setDestinationCrs(project.crs())
    ms.setLayers(layers)
    ms.setExtent(extent)
    ms.setOutputSize(QSize(*px))
    ms.setBackgroundColor(QColor("white"))
    job = QgsMapRendererParallelJob(ms)
    job.start()
    job.waitForFinished()
    job.renderedImage().save(str(OUT / fname))
    print("rendered", fname)


check = [gaps, bundle, hyd, osm, douro]
for b in bm.bookmarks():
    name = unicodedata.normalize("NFKD", b.name().lower()).encode("ascii", "ignore").decode()
    slug = "_".join("".join(c if c.isalnum() else " " for c in name).split())
    render(f"qgis_{slug}.png", b.extent(), check + [osm_tiles])
water_png = project.mapLayersByName("map-water.png")[0]
render("qgis_water_png_on_osm.png", bm.bookmarks()[-1].extent(), [bundle, osm, water_png, osm_tiles])

qgs.exitQgis()
