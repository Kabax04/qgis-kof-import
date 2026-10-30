"""Tester av eksport til KOF. Krever QGIS, hoppes over ellers."""

import pytest

qgis_core = pytest.importorskip("qgis.core")

from qgis.core import (  # noqa: E402
    QgsFeature,
    QgsGeometry,
    QgsPoint,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsVectorLayer,
)

from conftest import DATA, NGI  # noqa: E402
from kof_tools.kof_parser import parse_file  # noqa: E402
from kof_tools.processing.export_kof_algorithm import ExportKofAlgorithm  # noqa: E402
from kof_tools.processing.import_kof_algorithm import ImportKofAlgorithm  # noqa: E402

pytestmark = pytest.mark.usefixtures("qgis_app")


class CollectingFeedback(QgsProcessingFeedback):
    def __init__(self):
        super().__init__()
        self.warnings = []
        self.infos = []

    def pushWarning(self, warning):  # noqa: N802
        self.warnings.append(warning)
        super().pushWarning(warning)

    def pushInfo(self, info):  # noqa: N802
        self.infos.append(info)
        super().pushInfo(info)


def import_kof(path):
    alg = ImportKofAlgorithm().create()
    context = QgsProcessingContext()
    results, ok = alg.run({"INPUT": str(path), "OUTPUT": "memory:"}, context, QgsProcessingFeedback())
    assert ok
    return context.takeResultLayer(results["OUTPUT"])


def export_kof(layer, path, **params):
    alg = ExportKofAlgorithm().create()
    feedback = CollectingFeedback()
    results, ok = alg.run(
        {"INPUT": layer, "OUTPUT": str(path), **params}, QgsProcessingContext(), feedback
    )
    assert ok
    assert results["OUTPUT"] == str(path)
    return parse_file(path), feedback


def memory_layer(definition, fields="", features=()):
    layer = QgsVectorLayer(f"{definition}?crs=EPSG:25832{fields}", "målepunkter", "memory")
    provider = layer.dataProvider()
    for geometry, attributes in features:
        feature = QgsFeature(layer.fields())
        if geometry is not None:
            feature.setGeometry(geometry)
        feature.setAttributes(attributes)
        provider.addFeatures([feature])
    return layer


@pytest.mark.parametrize(
    "path", [DATA / "topcon_ovingsfil.kof", NGI / "UTM32_EN.kof", NGI / "KOF_from_ArcGIS.kof"], ids=lambda p: p.name
)
def test_import_eksport_import(path, tmp_path):
    original = parse_file(path)
    layer = import_kof(path)
    result, feedback = export_kof(layer, tmp_path / "ut.kof")
    assert feedback.warnings == []
    assert [(p.name, p.code, p.north, p.east, p.height, p.bk, p.remark) for p in result.points] == [
        (p.name, p.code, pytest.approx(p.north), pytest.approx(p.east), p.height, p.bk, p.remark)
        for p in original.points
    ]
    assert import_kof(tmp_path / "ut.kof").crs() == layer.crs()


def test_hode_har_sosi_kode_og_lagnavn(tmp_path):
    layer = memory_layer("Point", features=[(QgsGeometry(QgsPoint(599667.952, 6615798.981)), [])])
    result, _ = export_kof(layer, tmp_path / "ut.kof")
    assert result.header.crs_code == 22
    assert result.header.job == "målepunkter"
    assert result.header.east_first is False
    assert result.encoding == "cp1252"


def test_lag_uten_importfelt_bruker_nummer_og_z(tmp_path):
    layer = memory_layer("PointZ", features=[
        (QgsGeometry(QgsPoint(599667.952, 6615798.981, 98.848)), []),
        (QgsGeometry(QgsPoint(599670.0, 6615800.0, 99.5)), []),
    ])
    result, feedback = export_kof(layer, tmp_path / "ut.kof")
    assert [(p.name, p.north, p.east, p.height) for p in result.points] == [
        ("1", 6615798.981, 599667.952, 98.848),
        ("2", 6615800.0, 599670.0, 99.5),
    ]
    assert "The layer has no field name, not used" in feedback.infos


def test_valgte_felt(tmp_path):
    layer = memory_layer(
        "Point", "&field=id:string&field=tema:integer&field=kote:double&field=notat:string",
        [(QgsGeometry(QgsPoint(599667.952, 6615798.981)), ["K1", 2000, 12.5, "kum"])],
    )
    result, _ = export_kof(
        layer, tmp_path / "ut.kof",
        NAME_FIELD="id", CODE_FIELD="tema", HEIGHT_FIELD="kote", BK_FIELD=None, REMARK_FIELD="notat",
    )
    (p,) = result.points
    assert (p.name, p.code, p.height, p.remark) == ("K1", "2000", 12.5, "kum")


def test_null_verdier(tmp_path):
    layer = memory_layer(
        "Point", "&field=name:string&field=code:string&field=H:double",
        [(QgsGeometry(QgsPoint(599667.952, 6615798.981)), ["P1", None, None])],
    )
    result, feedback = export_kof(layer, tmp_path / "ut.kof")
    (p,) = result.points
    assert (p.name, p.code, p.height) == ("P1", "", None)
    assert feedback.warnings == []


def test_transformerer_til_valgt_crs(tmp_path):
    layer = import_kof(DATA / "topcon_ovingsfil.kof")
    result, feedback = export_kof(layer, tmp_path / "ut.kof", TARGET_CRS="EPSG:25833")
    assert result.header.crs_code == 23
    original = parse_file(DATA / "topcon_ovingsfil.kof").points[0]
    # The same point is further east in zone 32 than in zone 33.
    assert result.points[0].east < original.east
    assert any("EPSG:25833" in info for info in feedback.infos)


def test_geografisk_crs_avvises(tmp_path):
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "wgs84", "memory")
    alg = ExportKofAlgorithm().create()
    with pytest.raises(QgsProcessingException):
        alg.processAlgorithm(
            {"INPUT": layer, "OUTPUT": str(tmp_path / "ut.kof")}, QgsProcessingContext(), QgsProcessingFeedback()
        )


def test_geografisk_lag_med_projisert_maal(tmp_path):
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "wgs84", "memory")
    feature = QgsFeature(layer.fields())
    feature.setGeometry(QgsGeometry(QgsPoint(10.75, 59.91)))
    layer.dataProvider().addFeatures([feature])
    result, _ = export_kof(layer, tmp_path / "ut.kof", TARGET_CRS="EPSG:25832")
    (p,) = result.points
    assert p.north == pytest.approx(6643000, abs=2000)
    assert p.east == pytest.approx(597000, abs=2000)


def test_crs_uten_sosi_kode_gir_advarsel(tmp_path):
    layer = import_kof(DATA / "topcon_ovingsfil.kof")
    result, feedback = export_kof(layer, tmp_path / "ut.kof", TARGET_CRS="EPSG:3006")
    assert result.header.crs_code is None
    assert result.metadata["EPSG"] == "3006"
    assert any("SOSI" in w for w in feedback.warnings)


def test_multipunkt_og_manglende_geometri(tmp_path):
    layer = memory_layer("MultiPoint", "&field=name:string", [
        (QgsGeometry.fromWkt("MultiPoint ((1000 2000), (1001 2001))"), ["M"]),
        (None, ["tom"]),
    ])
    result, feedback = export_kof(layer, tmp_path / "ut.kof")
    assert [(p.name, p.north, p.east) for p in result.points] == [("M", 2000, 1000), ("M", 2001, 1001)]
    assert feedback.warnings == ["1 point(s) without north or east coordinate were skipped, e.g. 'tom'"]


def test_utf8(tmp_path):
    layer = memory_layer(
        "Point", "&field=name:string", [(QgsGeometry(QgsPoint(1000, 2000)), ["Ω1"])],
    )
    result, feedback = export_kof(layer, tmp_path / "ut.kof", ENCODING=1)
    assert result.encoding == "utf-8-sig"
    assert result.points[0].name == "Ω1"
    assert feedback.warnings == []
