from pathlib import Path

import pytest

from kof_import.kof_parser import parse_file

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def topcon():
    return parse_file(DATA / "topcon_ovingsfil.kof")


@pytest.fixture(scope="session")
def qgis_app():
    """Én QgsApplication for hele testkjøringen; QGIS tåler ikke å starte to ganger."""
    qgis_core = pytest.importorskip("qgis.core")
    app = qgis_core.QgsApplication([], False)
    app.initQgis()
    yield app
    app.exitQgis()
