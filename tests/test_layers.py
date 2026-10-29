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


def run_algorithm_all(params):
    alg = ImportKofAlgorithm().create()
    context = QgsProcessingContext()
    params = {"OUTPUT": "memory:", "OUTPUT_GROUPS": "memory:", **params}
    results, ok = alg.run(params, context, QgsProcessingFeedback())
    assert ok
    return results, context


def test_middellag_med_enkeltpunkter():
    results, context = run_algorithm_all({"INPUT": str(DATA / "topcon_ovingsfil.kof")})
    layer = context.takeResultLayer(results["OUTPUT_GROUPS"])
    assert layer.featureCount() == 11
    assert QgsWkbTypes.hasZ(layer.wkbType())
    group = next(f for f in layer.getFeatures() if f["navn"] == "104")
    assert group["navn_liste"] == "104,105,106"
    assert group["antall"] == 3
    assert group.geometry().constGet().x() == pytest.approx(group["E"])


def test_middellag_bare_gjentatte():
    results, context = run_algorithm_all(
        {"INPUT": str(DATA / "topcon_ovingsfil.kof"), "INCLUDE_SINGLES": False}
    )
    layer = context.takeResultLayer(results["OUTPUT_GROUPS"])
    assert layer.featureCount() == 5


def test_hoydetoleranse_splitter_grupper():
    # Høydene i 115/117/120 spriker 32 mm, så 1 cm høydetoleranse deler gruppen.
    results, context = run_algorithm_all(
        {
            "INPUT": str(DATA / "topcon_ovingsfil.kof"),
            "INCLUDE_SINGLES": False,
            "HEIGHT_TOLERANCE": 0.01,
        }
    )
    layer = context.takeResultLayer(results["OUTPUT_GROUPS"])
    names = {f["navn_liste"] for f in layer.getFeatures()}
    assert "115,117,120" not in names


def test_middellag_kan_droppes():
    alg = ImportKofAlgorithm().create()
    context = QgsProcessingContext()
    params = {
        "INPUT": str(DATA / "topcon_ovingsfil.kof"),
        "OUTPUT": "memory:",
        "OUTPUT_GROUPS": None,
    }
    results, ok = alg.run(params, context, QgsProcessingFeedback())
    assert ok
    assert "OUTPUT_GROUPS" not in results
