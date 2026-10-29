"""Bygg QGIS-objekter fra parser-resultatet.

Her byttes KOFs N/Ø til QGIS sin x = Ø, y = N.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Optional

from qgis.core import (
    Qgis,
    QgsCircularString,
    QgsCoordinateReferenceSystem,
    QgsLineString,
    QgsPolygon,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsGeometryUtils,
    QgsPoint,
    QgsVectorLayer,
    QgsWkbTypes,
)
from .duplicates import PointGroup
from .kof_lines import KofLine
from .kof_parser import KofResult

POINT_WKB_TYPE = QgsWkbTypes.PointZ
LINE_WKB_TYPE = QgsWkbTypes.LineStringZ
POLYGON_WKB_TYPE = QgsWkbTypes.PolygonZ

# QGIS 3.38 gikk over fra QVariant til QMetaType for felttyper.
if Qgis.QGIS_VERSION_INT >= 33800:
    from qgis.PyQt.QtCore import QMetaType

    STRING, DOUBLE, INT = QMetaType.Type.QString, QMetaType.Type.Double, QMetaType.Type.Int
else:
    from qgis.PyQt.QtCore import QVariant

    STRING, DOUBLE, INT = QVariant.String, QVariant.Double, QVariant.Int


def point_fields() -> QgsFields:
    fields = QgsFields()
    fields.append(QgsField("navn", STRING))
    fields.append(QgsField("kode", STRING))
    fields.append(QgsField("N", DOUBLE))
    fields.append(QgsField("E", DOUBLE))
    fields.append(QgsField("H", DOUBLE))
    fields.append(QgsField("bk", INT))
    fields.append(QgsField("merknad", STRING))
    fields.append(QgsField("linjenr", INT))
    fields.append(QgsField("kildefil", STRING))
    return fields


def point_features(result: KofResult, fields: QgsFields) -> Iterator[QgsFeature]:
    source = Path(result.source).name if result.source else None
    for p in result.points:
        feature = QgsFeature(fields)
        z = p.height if p.height is not None else float("nan")
        feature.setGeometry(QgsGeometry(QgsPoint(p.east, p.north, z)))
        feature.setAttributes([
            p.name, p.code, p.north, p.east, p.height, p.bk, p.remark, p.line_no, source
        ])
        yield feature


def group_fields() -> QgsFields:
    fields = QgsFields()
    fields.append(QgsField("gruppe", INT))
    fields.append(QgsField("navn", STRING))
    fields.append(QgsField("navn_liste", STRING))
    fields.append(QgsField("antall", INT))
    fields.append(QgsField("N", DOUBLE))
    fields.append(QgsField("E", DOUBLE))
    fields.append(QgsField("H", DOUBLE))
    fields.append(QgsField("std_N", DOUBLE))
    fields.append(QgsField("std_E", DOUBLE))
    fields.append(QgsField("std_H", DOUBLE))
    fields.append(QgsField("maks_avvik", DOUBLE))
    fields.append(QgsField("kildefil", STRING))
    return fields


def group_features(
    groups: List[PointGroup], fields: QgsFields, source: Optional[str] = None
) -> Iterator[QgsFeature]:
    """Ett objekt per gruppe, plassert i middelpunktet. `navn` er første måling."""
    source = Path(source).name if source else None
    for number, g in enumerate(groups, start=1):
        feature = QgsFeature(fields)
        z = g.height if g.height is not None else float("nan")
        feature.setGeometry(QgsGeometry(QgsPoint(g.east, g.north, z)))
        feature.setAttributes([
            number,
            g.members[0].name,
            ",".join(g.names),
            len(g.members),
            g.north,
            g.east,
            g.height,
            g.std_north,
            g.std_east,
            g.std_height,
            g.max_deviation,
            source,
        ])
        yield feature


def line_fields() -> QgsFields:
    """Felles felt for linje- og flatelaget."""
    fields = QgsFields()
    fields.append(QgsField("navn", STRING))
    fields.append(QgsField("type", STRING))
    fields.append(QgsField("kode", STRING))
    fields.append(QgsField("antall", INT))
    fields.append(QgsField("punkter", STRING))
    fields.append(QgsField("pi", INT))
    fields.append(QgsField("linjenr", INT))
    fields.append(QgsField("kildefil", STRING))
    return fields


def _vertex(p) -> QgsPoint:
    return QgsPoint(p.east, p.north, p.height if p.height is not None else float("nan"))


def line_geometry(line: KofLine) -> QgsGeometry:
    """LineStringZ gjennom punktene. Buer (09 93) blir segmentert sirkelbue.

    En sirkelbue i QGIS trenger et oddetall punkter (start, midt, slutt, midt,
    slutt, ...). Med et partall punkter følger buen alle unntatt det siste,
    og den siste biten tegnes som bue rundt sentrum til de tre siste punktene.
    """
    vertices = [_vertex(p) for p in line.points]
    if line.kind != "bue" or len(vertices) < 3:
        return QgsGeometry(QgsLineString(vertices))
    arc_vertices = vertices if len(vertices) % 2 else vertices[:-1]
    arc = QgsCircularString()
    arc.setPoints(arc_vertices)
    segmented = arc.curveToLine()
    if len(arc_vertices) < len(vertices):
        a, b, c = vertices[-3:]
        _, cx, cy = QgsGeometryUtils.circleCenterRadius(a, b, c)
        tail = QgsCircularString.fromTwoPointsAndCenter(b, c, QgsPoint(cx, cy), True)
        for vertex in list(tail.curveToLine().vertices())[1:]:
            segmented.addVertex(vertex)
        # Endepunktet skal være det målte punktet, med høyde.
        segmented.setZAt(segmented.numPoints() - 1, c.z())
    return QgsGeometry(segmented)


def polygon_geometry(line: KofLine) -> QgsGeometry:
    vertices = [_vertex(p) for p in line.points]
    polygon = QgsPolygon()
    polygon.setExteriorRing(QgsLineString(vertices + [vertices[0]]))
    return QgsGeometry(polygon)


def line_features(
    lines: List[KofLine], fields: QgsFields, source: Optional[str] = None
) -> Iterator[QgsFeature]:
    source = Path(source).name if source else None
    for line in lines:
        feature = QgsFeature(fields)
        feature.setGeometry(polygon_geometry(line) if line.closed else line_geometry(line))
        names = [p.name for p in line.points]
        feature.setAttributes([
            f"{names[0]}–{names[-1]}",
            "polygon" if line.closed else line.kind,
            line.points[0].code,
            len(names),
            ",".join(names),
            line.pi,
            line.line_no,
            source,
        ])
        yield feature


def build_point_layer(
    result: KofResult, crs: QgsCoordinateReferenceSystem, name: str = "KOF-punkter"
) -> QgsVectorLayer:
    """Lag et midlertidig PointZ-lag med alle punktene."""
    layer = QgsVectorLayer(f"PointZ?crs={crs.authid()}", name, "memory")
    fields = point_fields()
    provider = layer.dataProvider()
    provider.addAttributes(list(fields))
    layer.updateFields()
    provider.addFeatures(list(point_features(result, layer.fields())))
    layer.updateExtents()
    return layer
