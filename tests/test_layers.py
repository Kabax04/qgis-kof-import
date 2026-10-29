"""Tester som krever QGIS. Hoppes over når qgis ikke kan importeres.

Kjør med QGIS sin Python, f.eks. `python-qgis-ltr.bat -m pytest`.
"""

import pytest

qgis_core = pytest.importorskip("qgis.core")

from qgis.core import (  # noqa: E402
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsWkbTypes,
)

from conftest import DATA  # noqa: E402
from kof_import.layer_builder import build_point_layer  # noqa: E402
from kof_import.processing.import_kof_algorithm import ImportKofAlgorithm  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def qgis_app():
    app = QgsApplication([], False)
    app.initQgis()
    yield app
    app.exitQgis()


def run_algorithm(params):
    alg = ImportKofAlgorithm().create()
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    params = {"OUTPUT": "memory:", **params}
    results, ok = alg.run(params, context, feedback)
    assert ok
    # Ta over eierskapet, ellers slettes laget sammen med konteksten.
    return context.takeResultLayer(results["OUTPUT"])


def test_build_point_layer(topcon):
    layer = build_point_layer(topcon, QgsCoordinateReferenceSystem("EPSG:25832"))
    assert layer.isValid()
    assert layer.featureCount() == 21
    assert QgsWkbTypes.hasZ(layer.wkbType())


def test_x_er_ost_y_er_nord(topcon):
    layer = build_point_layer(topcon, QgsCoordinateReferenceSystem("EPSG:25832"))
    feature = next(layer.getFeatures())
    point = feature.geometry().constGet()
    assert feature["navn"] == "100"
    assert point.x() == pytest.approx(599667.952)
    assert point.y() == pytest.approx(6615798.981)
    assert point.z() == pytest.approx(98.848)


def test_algoritme_finner_crs_fra_filen():
    layer = run_algorithm({"INPUT": str(DATA / "topcon_ovingsfil.kof")})
    assert layer.crs().authid() == "EPSG:25832"
    assert layer.featureCount() == 21


def test_algoritme_valgt_crs_overstyrer():
    layer = run_algorithm(
        {"INPUT": str(DATA / "topcon_ovingsfil.kof"), "CRS": "EPSG:25833"}
    )
    assert layer.crs().authid() == "EPSG:25833"


def test_algoritme_uten_crs_feiler(tmp_path):
    path = tmp_path / "uten_crs.kof"
    path.write_text(" 05 P1                  6615798.981  599667.952   98.848\n")
    alg = ImportKofAlgorithm().create()
    with pytest.raises(QgsProcessingException):
        alg.processAlgorithm(
            {"INPUT": str(path), "OUTPUT": "memory:"},
            QgsProcessingContext(),
            QgsProcessingFeedback(),
        )
