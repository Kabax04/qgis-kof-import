"""Bygg QGIS-objekter fra parser-resultatet.

Her byttes KOFs N/Ø til QGIS sin x = Ø, y = N.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Optional

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPoint,
    QgsVectorLayer,
    QgsWkbTypes,
)
from .duplicates import PointGroup
from .kof_parser import KofResult

POINT_WKB_TYPE = QgsWkbTypes.PointZ

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
    fields.append(QgsField("linjenr", INT))
    fields.append(QgsField("kildefil", STRING))
    return fields


def point_features(result: KofResult, fields: QgsFields) -> Iterator[QgsFeature]:
    source = Path(result.source).name if result.source else None
    for p in result.points:
        feature = QgsFeature(fields)
        z = p.height if p.height is not None else float("nan")
        feature.setGeometry(QgsGeometry(QgsPoint(p.east, p.north, z)))
        feature.setAttributes([p.name, p.code, p.north, p.east, p.height, p.line_no, source])
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
