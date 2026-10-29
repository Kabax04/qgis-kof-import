"""Tester av stil og dra-og-slipp. Krever QGIS og Processing-pluginen."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("qgis.gui")

from qgis.core import (  # noqa: E402
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsProject,
)

from conftest import DATA  # noqa: E402
from kof_import.drop_handler import KofDropHandler  # noqa: E402
from kof_import.layer_builder import build_point_layer  # noqa: E402
from kof_import.layer_style import style_groups, style_points  # noqa: E402
from kof_import.processing.provider import KofProvider  # noqa: E402

pytestmark = pytest.mark.usefixtures("qgis_app")


class FakeMessageBar:
    def __init__(self):
        self.messages = []

    def pushMessage(self, title, text, *args, level=Qgis.Info):  # noqa: N802
        self.messages.append((text, args, level))


class FakeIface:
    def __init__(self):
        self.bar = FakeMessageBar()

    def messageBar(self):  # noqa: N802
        return self.bar


@pytest.fixture(scope="module")
def processing_ready(qgis_app):
    sys.path.append(str(Path(QgsApplication.prefixPath()) / "python" / "plugins"))
    from processing.core.Processing import Processing

    Processing.initialize()
    provider = KofProvider()
    QgsApplication.processingRegistry().addProvider(provider)
    yield
    QgsApplication.processingRegistry().removeProvider(provider)


@pytest.fixture
def project():
    QgsProject.instance().clear()
    yield QgsProject.instance()
    QgsProject.instance().clear()


def test_stil_punkter(topcon):
    layer = build_point_layer(topcon, QgsCoordinateReferenceSystem("EPSG:25832"))
    style_points(layer)
    assert layer.labelsEnabled()
    assert layer.labeling().settings().fieldName == "navn"


def test_stil_grupper(topcon):
    layer = build_point_layer(topcon, QgsCoordinateReferenceSystem("EPSG:25832"))
    style_groups(layer)
    assert layer.labeling().settings().fieldName == "navn_liste"


def test_drop_ignorerer_andre_filer():
    assert KofDropHandler(FakeIface()).handleFileDrop("kart.shp") is False


@pytest.mark.usefixtures("processing_ready")
def test_drop_kof_laster_stilte_lag(project):
    iface = FakeIface()
    assert KofDropHandler(iface).handleFileDrop(str(DATA / "topcon_ovingsfil.kof"))

    layers = {layer.name(): layer for layer in project.mapLayers().values()}
    assert set(layers) == {"topcon_ovingsfil", "topcon_ovingsfil (middel)"}
    assert layers["topcon_ovingsfil"].featureCount() == 21
    assert layers["topcon_ovingsfil"].labeling().settings().fieldName == "navn"
    assert layers["topcon_ovingsfil (middel)"].labeling().settings().fieldName == "navn_liste"

    # 102 og 108 ligger like utenfor toleransen og gir en advarsel.
    (text, details, level), = iface.bar.messages
    assert level == Qgis.Warning
    assert "1 advarsel." in text
    assert "102 og 108" in details[0]


@pytest.mark.usefixtures("processing_ready")
def test_drop_uten_crs_aapner_dialog(project, tmp_path, monkeypatch):
    import processing

    opened = []
    monkeypatch.setattr(
        processing, "execAlgorithmDialog", lambda alg, params: opened.append(params)
    )
    path = tmp_path / "uten_crs.kof"
    path.write_text(" 05 P1                  6615798.981  599667.952   98.848\n")

    assert KofDropHandler(FakeIface()).handleFileDrop(str(path))
    assert opened == [{"INPUT": str(path)}]
    assert project.count() == 0


@pytest.mark.usefixtures("processing_ready")
def test_drop_med_linjer_laster_fire_lag(project, tmp_path):
    # Spesifikasjonsfilen har lokale koordinater; et 01-hode gir den et CRS.
    header = " 01 LINJETEST    29102026   2      22      $11100000000\n"
    text = (DATA / "spec_linjer.kof").read_text(encoding="cp1252")
    path = tmp_path / "linjer.kof"
    path.write_text(header + text, encoding="cp1252")

    assert KofDropHandler(FakeIface()).handleFileDrop(str(path))

    layers = {layer.name(): layer for layer in project.mapLayers().values()}
    assert set(layers) == {"linjer", "linjer (middel)", "linjer (linjer)", "linjer (flater)"}
    assert layers["linjer (linjer)"].featureCount() == 9
    assert layers["linjer (flater)"].featureCount() == 1
    assert layers["linjer (linjer)"].crs().authid() == "EPSG:25832"
