from pathlib import Path

import pytest

from kof_tools import i18n
from kof_tools.kof_parser import parse_file

DATA = Path(__file__).parent / "data"
NGI = DATA / "ngi"


@pytest.fixture(autouse=True)
def english():
    """Tests run in English unless they switch language themselves."""
    i18n.set_language("en")
    yield
    i18n.set_language("en")


@pytest.fixture(scope="session")
def topcon():
    return parse_file(DATA / "topcon_ovingsfil.kof")


@pytest.fixture(scope="session")
def qgis_app():
    """One QgsApplication for the whole test run; QGIS cannot be started twice."""
    qgis_core = pytest.importorskip("qgis.core")
    app = qgis_core.QgsApplication([], False)
    app.initQgis()
    yield app
    app.exitQgis()
